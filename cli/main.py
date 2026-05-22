"""CLI for the cs-agent harness.

Three commands:
  smoke    Run one scenario with the Mock provider; no API keys required.
  run      Run one scenario with the configured provider; writes a trace.
  eval     Run all scenarios + graders + report.

Loads .env at startup. Provider selection driven by AGENT_PROVIDER and
JUDGE_PROVIDER env vars (see .env.example).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = REPO_ROOT / "evals" / "scenarios"


def main(argv: Optional[List[str]] = None) -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="cs-agent",
        description="FI-CAST customer service triage agent: harness + evals.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    smoke_p = sub.add_parser(
        "smoke",
        help="Run one scenario with the Mock provider (zero spend, no API key required).",
    )
    smoke_p.add_argument(
        "--scenario",
        default="outage_with_active_incident",
        help="Scenario ID (filename without .yaml). Default: outage_with_active_incident.",
    )

    run_p = sub.add_parser(
        "run",
        help="Run one scenario with the configured provider; writes a trace to traces/.",
    )
    run_p.add_argument("--scenario", required=True, help="Scenario ID (filename without .yaml).")

    sub.add_parser(
        "eval",
        help="Run all scenarios, grade each, and write a markdown report to reports/.",
    )

    args = parser.parse_args(argv)

    if args.command == "smoke":
        return cmd_smoke(args.scenario)
    if args.command == "run":
        return cmd_run(args.scenario)
    if args.command == "eval":
        return cmd_eval()

    parser.print_help()
    return 1


def cmd_smoke(scenario_id: str) -> int:
    """Force the Mock provider; verify the harness end to end with zero spend."""
    print(f"[smoke] Running '{scenario_id}' with Mock provider (no API key required)...")

    # Override provider env regardless of .env settings
    os.environ["AGENT_PROVIDER"] = "mock"
    os.environ["JUDGE_PROVIDER"] = "mock"

    scenario = _load_scenario_yaml(scenario_id)
    if not scenario:
        print(f"[smoke] Scenario '{scenario_id}' not found in {SCENARIOS_DIR}.", file=sys.stderr)
        return 1

    from harness.runner import run_and_save

    try:
        trace, path = run_and_save(
            scenario_id=scenario_id,
            customer_id=scenario["input"]["customer_id"],
            customer_message=scenario["input"]["customer_message"],
        )
    except Exception as e:
        print(f"[smoke] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    if trace.error:
        print(f"[smoke] FAILED: {trace.error}", file=sys.stderr)
        return 1
    if not trace.final_output:
        print(f"[smoke] FAILED: no final output produced", file=sys.stderr)
        return 1

    print(f"[smoke] OK: harness end-to-end works.")
    print(f"[smoke] Trace: {path}")
    print(f"[smoke] Turns: {len(trace.turns)}, tool calls: {len(trace.tool_invocations)}")
    print(f"[smoke] Final recommended_action: {trace.final_output.get('recommended_action')}")
    return 0


def cmd_run(scenario_id: str) -> int:
    """Run one scenario with the agent provider configured in .env."""
    print(f"[run] Running '{scenario_id}'...")

    scenario = _load_scenario_yaml(scenario_id)
    if not scenario:
        print(f"[run] Scenario '{scenario_id}' not found in {SCENARIOS_DIR}.", file=sys.stderr)
        return 1

    from harness.runner import run_and_save

    try:
        trace, path = run_and_save(
            scenario_id=scenario_id,
            customer_id=scenario["input"]["customer_id"],
            customer_message=scenario["input"]["customer_message"],
        )
    except Exception as e:
        print(f"[run] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    print(f"[run] Provider: {trace.agent_provider} ({trace.agent_model})")
    print(f"[run] Trace: {path}")
    if trace.error:
        print(f"[run] WARNING: {trace.error}")
    if trace.final_output:
        print(f"[run] Final output:")
        print(json.dumps(trace.final_output, indent=2, ensure_ascii=False))
    print(f"[run] Turns: {len(trace.turns)}, tool calls: {len(trace.tool_invocations)}")
    print(f"[run] Latency: {trace.total_latency_ms}ms")
    if trace.total_input_tokens:
        print(f"[run] Tokens in/out: {trace.total_input_tokens} / {trace.total_output_tokens}")
    return 0


def cmd_eval() -> int:
    """Run every scenario, grade each, build the markdown report."""
    print(f"[eval] Loading scenarios and running with configured providers...")

    from evals.runner import evaluate_all

    try:
        result = evaluate_all()
    except Exception as e:
        print(f"[eval] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    if "error" in result:
        print(f"[eval] {result['error']}", file=sys.stderr)
        return 1

    summary = result["summary"]
    print()
    print(f"  Agent:  {result['agent']['provider']} ({result['agent']['model']})")
    print(f"  Judge:  {result['judge']['provider']} ({result['judge']['model']})")
    print()
    print(f"  Scenarios run:        {summary['scenarios_run']}")
    print(f"  Grader checks total:  {summary['total_grader_checks']}")
    print(f"  Passes:               {summary['total_passes']}")
    print(f"  Failures:             {summary['total_fails']}")
    print(f"  Overall pass rate:    {summary['overall_pass_rate'] * 100:.1f}%")
    print()
    print(f"  Report:  {result['report_path']}")
    print()
    return 0


def _load_scenario_yaml(scenario_id: str) -> Optional[Dict[str, Any]]:
    import yaml
    path = SCENARIOS_DIR / f"{scenario_id}.yaml"
    if not path.exists():
        return None
    with path.open() as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    sys.exit(main())
