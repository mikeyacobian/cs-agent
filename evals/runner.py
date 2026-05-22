"""Eval runner: load scenarios, run agent, run graders, write report.

Eval mode is `run` mode plus grading. Same harness, same trace schema,
plus six grader results per trace and an aggregate markdown report.

Reports land in `reports/<timestamp>.md` (gitignored).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from evals.graders import GraderResult
from evals.graders.code_based import (
    grade_credit_amount,
    grade_issue_type,
    grade_policy_citations,
    grade_recommended_action,
    grade_required_tools,
)
from evals.graders.model_based import grade_customer_response
from harness.providers import ModelProvider, create_provider
from harness.runner import run_and_save
from harness.trace import Trace

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = REPO_ROOT / "evals" / "scenarios"
REPORTS_DIR = REPO_ROOT / "reports"


@dataclass
class ScenarioResult:
    """Aggregated graders for one scenario."""

    scenario_id: str
    customer_id: str
    trace_path: str
    trace_run_id: str
    final_output: Optional[Dict[str, Any]]
    grader_results: List[GraderResult] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def pass_count(self) -> int:
        return sum(1 for g in self.grader_results if g.passed and not g.skipped)

    @property
    def fail_count(self) -> int:
        return sum(1 for g in self.grader_results if not g.passed and not g.skipped)

    @property
    def total_graded(self) -> int:
        return sum(1 for g in self.grader_results if not g.skipped)

    @property
    def pass_rate(self) -> float:
        return self.pass_count / max(self.total_graded, 1)


def load_scenarios() -> List[Dict[str, Any]]:
    """Load every YAML scenario from evals/scenarios/."""
    scenarios = []
    for yml in sorted(SCENARIOS_DIR.glob("*.yaml")):
        with yml.open() as f:
            scenarios.append(yaml.safe_load(f))
    return scenarios


def evaluate_scenario(
    scenario: Dict[str, Any],
    agent_provider: Optional[ModelProvider] = None,
    judge_provider: Optional[ModelProvider] = None,
) -> ScenarioResult:
    """Run one scenario through the harness, then run graders against the trace."""

    customer_id = scenario["input"]["customer_id"]
    customer_message = scenario["input"]["customer_message"]
    scenario_id = scenario["id"]

    trace, trace_path = run_and_save(
        scenario_id=scenario_id,
        customer_id=customer_id,
        customer_message=customer_message,
        agent_provider=agent_provider,
    )

    grader_results: List[GraderResult] = []

    if trace.error or not trace.final_output:
        grader_results.append(GraderResult(
            grader_name="harness_run",
            passed=False,
            score=0.0,
            explanation=trace.error or "No final output produced.",
        ))
        return ScenarioResult(
            scenario_id=scenario_id,
            customer_id=customer_id,
            trace_path=str(trace_path),
            trace_run_id=trace.run_id,
            final_output=trace.final_output,
            grader_results=grader_results,
            error=trace.error,
        )

    # Code-based graders
    grader_results.append(grade_issue_type(scenario, trace))
    grader_results.append(grade_recommended_action(scenario, trace))
    grader_results.append(grade_required_tools(scenario, trace))
    grader_results.append(grade_policy_citations(scenario, trace))
    grader_results.append(grade_credit_amount(scenario, trace))

    # Model-based grader (LLM-as-judge)
    try:
        grader_results.append(
            grade_customer_response(scenario, trace, judge=judge_provider)
        )
    except Exception as e:
        grader_results.append(GraderResult(
            grader_name="customer_response_quality",
            passed=False,
            score=0.0,
            explanation=f"Judge invocation failed: {type(e).__name__}: {e}",
        ))

    # Attach grader summary to the trace and persist
    trace.eval_result = {
        "graders": [asdict(g) for g in grader_results],
    }
    # Re-write the trace with the eval result attached
    from harness.trace import write_trace
    write_trace(trace, REPO_ROOT / "traces")

    return ScenarioResult(
        scenario_id=scenario_id,
        customer_id=customer_id,
        trace_path=str(trace_path),
        trace_run_id=trace.run_id,
        final_output=trace.final_output,
        grader_results=grader_results,
    )


def evaluate_all(
    agent_provider: Optional[ModelProvider] = None,
    judge_provider: Optional[ModelProvider] = None,
) -> Dict[str, Any]:
    """Run every scenario, grade each, write a markdown report."""

    scenarios = load_scenarios()
    if not scenarios:
        return {
            "error": f"No scenarios found in {SCENARIOS_DIR}",
            "results": [],
        }

    agent = agent_provider or create_provider("agent")
    judge = judge_provider or create_provider("judge")

    results: List[ScenarioResult] = []
    for scenario in scenarios:
        results.append(evaluate_scenario(scenario, agent_provider=agent, judge_provider=judge))

    report_path = _write_report(results, agent, judge)

    total_graders = sum(r.total_graded for r in results)
    total_passes = sum(r.pass_count for r in results)
    total_fails = sum(r.fail_count for r in results)

    return {
        "results": [asdict(r) for r in results],
        "report_path": str(report_path),
        "summary": {
            "scenarios_run": len(results),
            "total_grader_checks": total_graders,
            "total_passes": total_passes,
            "total_fails": total_fails,
            "overall_pass_rate": total_passes / max(total_graders, 1),
        },
        "agent": {"provider": agent.name, "model": agent.model},
        "judge": {"provider": judge.name, "model": judge.model},
    }


def _write_report(
    results: List[ScenarioResult],
    agent: ModelProvider,
    judge: ModelProvider,
) -> Path:
    """Build the human-readable markdown report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    path = REPORTS_DIR / f"eval_report_{ts}.md"

    total_graders = sum(r.total_graded for r in results)
    total_passes = sum(r.pass_count for r in results)
    overall_pass_rate = total_passes / max(total_graders, 1)

    lines = [
        f"# Eval Report — {ts}",
        "",
        f"**Agent:** `{agent.name}` ({agent.model})  ",
        f"**Judge:** `{judge.name}` ({judge.model})",
        "",
        "## Summary",
        "",
        f"- Scenarios run: **{len(results)}**",
        f"- Grader checks: **{total_graders}**",
        f"- Passes: **{total_passes}**",
        f"- Failures: **{total_graders - total_passes}**",
        f"- Overall pass rate: **{overall_pass_rate * 100:.1f}%**",
        "",
        "## Per-scenario results",
        "",
    ]

    for r in results:
        lines.append(f"### Scenario: `{r.scenario_id}` (customer {r.customer_id})")
        lines.append("")
        if r.error:
            lines.append(f"**Run error:** {r.error}")
            lines.append("")
            lines.append(f"Trace: `{r.trace_path}`")
            lines.append("")
            continue
        action = r.final_output.get("recommended_action") if r.final_output else "(none)"
        issue = r.final_output.get("issue_type") if r.final_output else "(none)"
        conf = r.final_output.get("confidence") if r.final_output else None
        lines.append(
            f"**Final output:** issue_type=`{issue}`, recommended_action=`{action}`"
            + (f", confidence={conf}" if conf is not None else "")
        )
        lines.append("")
        lines.append(
            f"**Score:** {r.pass_count}/{r.total_graded} graders passed "
            f"({r.pass_rate * 100:.0f}%)"
        )
        lines.append("")
        lines.append("| Grader | Result | Explanation |")
        lines.append("|---|---|---|")
        for g in r.grader_results:
            if g.skipped:
                status = "SKIP"
            elif g.passed:
                status = "PASS"
            else:
                status = "FAIL"
            explanation = g.explanation.replace("\n", " ").replace("|", "\\|")
            lines.append(f"| `{g.grader_name}` | {status} | {explanation} |")
        lines.append("")
        lines.append(f"Trace file: `{r.trace_path}`")
        lines.append("")

    lines.append("## Failures across scenarios")
    lines.append("")
    failures: Dict[str, List[str]] = {}
    for r in results:
        for g in r.grader_results:
            if not g.passed and not g.skipped:
                failures.setdefault(g.grader_name, []).append(r.scenario_id)
    if not failures:
        lines.append("None. All graders passed across all scenarios.")
    else:
        for name, scens in sorted(failures.items(), key=lambda x: -len(x[1])):
            lines.append(f"- `{name}` failed in: {', '.join(scens)}")
    lines.append("")

    path.write_text("\n".join(lines))
    return path
