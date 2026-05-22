"""Trace schema and writer.

A Trace is the production observability contract of the agent. Every run,
whether in `run` mode (single scenario) or `eval` mode (corpus + graders),
produces a Trace with the same shape. Eval mode adds grader results; the
underlying trace is identical.

The trace is the load-bearing artifact for everything downstream:
- Eval graders consume traces and check them against scenario expectations.
- A human reviewer reads a trace to diagnose why an agent did what it did.
- The report aggregator builds summaries across many traces.

Traces land in `traces/` (gitignored) as one JSON file per run.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TurnCall:
    """One model call within a run."""

    turn_index: int
    input_messages_summary: str
    tool_calls_requested: List[Dict[str, Any]] = field(default_factory=list)
    text_output: Optional[str] = None
    stop_reason: str = ""
    latency_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


@dataclass
class ToolInvocation:
    """One tool call executed by the harness."""

    call_id: str
    name: str
    arguments: Dict[str, Any]
    result: Any
    is_error: bool = False
    timestamp: str = ""


@dataclass
class Trace:
    """One end-to-end run record."""

    run_id: str
    scenario_id: str
    timestamp: str
    agent_provider: str
    agent_model: str
    judge_provider: Optional[str] = None
    judge_model: Optional[str] = None

    input_message: str = ""
    customer_id: str = ""

    turns: List[TurnCall] = field(default_factory=list)
    tool_invocations: List[ToolInvocation] = field(default_factory=list)

    final_output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    total_latency_ms: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    eval_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def new_trace(
    scenario_id: str,
    customer_id: str,
    agent_provider: str,
    agent_model: str,
    judge_provider: Optional[str] = None,
    judge_model: Optional[str] = None,
) -> Trace:
    """Construct a Trace with a fresh run_id and current timestamp."""
    return Trace(
        run_id=str(uuid.uuid4()),
        scenario_id=scenario_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        agent_provider=agent_provider,
        agent_model=agent_model,
        judge_provider=judge_provider,
        judge_model=judge_model,
        customer_id=customer_id,
    )


def write_trace(trace: Trace, traces_dir: Path) -> Path:
    """Write trace to disk as JSON; returns the path written."""
    traces_dir.mkdir(parents=True, exist_ok=True)
    ts = trace.timestamp.replace(":", "-").replace(".", "-")
    filename = f"{ts}__{trace.scenario_id}__{trace.run_id[:8]}.json"
    path = traces_dir / filename
    path.write_text(json.dumps(trace.to_dict(), indent=2, default=str))
    return path
