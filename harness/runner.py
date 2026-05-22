"""Harness runner: the agent's runtime.

Two modes share this same code path:
- `run_scenario()`: one scenario, trace only. Production-shaped path.
- `evaluate()` in evals/runner.py: scenario corpus + graders + report.

Both produce traces with the same shape. Eval mode wraps run with grading.

The tool loop:
    while not final and turns < MAX_TURNS:
        result = provider.generate(system, messages, tools)
        if result.is_final:
            parse final output, break
        for tc in result.tool_calls:
            execute via dispatch(tc.name, tc.arguments)
            append tool result to messages
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent.tools import TOOL_SPECS, dispatch
from harness.providers import ModelProvider, create_provider
from harness.providers.base import Message, ToolResult
from harness.trace import (
    Trace,
    ToolInvocation,
    TurnCall,
    new_trace,
    write_trace,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SYSTEM_PROMPT_PATH = REPO_ROOT / "agent" / "system_prompt.md"
TRACES_DIR = REPO_ROOT / "traces"

MAX_TURNS = 8


def load_system_prompt() -> str:
    """Load the agent's system prompt from disk."""
    return SYSTEM_PROMPT_PATH.read_text()


def run_scenario(
    scenario_id: str,
    customer_id: str,
    customer_message: str,
    agent_provider: Optional[ModelProvider] = None,
) -> Trace:
    """Run the agent against one scenario; return a complete Trace.

    If agent_provider is None, the factory selects one from env vars.
    """
    provider = agent_provider or create_provider("agent")
    system_prompt = load_system_prompt()

    trace = new_trace(
        scenario_id=scenario_id,
        customer_id=customer_id,
        agent_provider=provider.name,
        agent_model=provider.model,
    )
    trace.input_message = customer_message

    # The agent receives both the customer's message and the customer_id
    # so it knows whose account to look up.
    user_message = f"Customer (id: {customer_id}) says:\n\n{customer_message}"
    messages: List[Message] = [Message(role="user", content=user_message)]

    final_output: Optional[Dict[str, Any]] = None
    final_reached = False
    for turn_index in range(MAX_TURNS):
        result = provider.generate(
            system=system_prompt,
            messages=messages,
            tools=TOOL_SPECS,
        )

        trace.turns.append(TurnCall(
            turn_index=turn_index,
            input_messages_summary=f"{len(messages)} messages",
            tool_calls_requested=[
                {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                for tc in result.tool_calls
            ],
            text_output=result.text,
            stop_reason=result.stop_reason,
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ))
        if result.latency_ms:
            trace.total_latency_ms += result.latency_ms
        if result.input_tokens:
            trace.total_input_tokens += result.input_tokens
        if result.output_tokens:
            trace.total_output_tokens += result.output_tokens

        if result.is_final:
            try:
                final_output = json.loads(result.text or "{}")
                trace.final_output = final_output
            except json.JSONDecodeError as e:
                trace.error = (
                    f"Final output not valid JSON: {e}; raw text: {result.text!r}"
                )
            final_reached = True
            break

        # Append the assistant turn (with tool calls)
        messages.append(Message(
            role="assistant",
            content=result.text or "",
            tool_calls=result.tool_calls,
        ))

        # Execute each tool call and append its result
        for tc in result.tool_calls:
            tool_result_value = dispatch(tc.name, tc.arguments)
            is_error = isinstance(tool_result_value, dict) and "error" in tool_result_value
            tr = ToolResult(
                call_id=tc.id,
                name=tc.name,
                result=tool_result_value,
                is_error=is_error,
            )
            trace.tool_invocations.append(ToolInvocation(
                call_id=tc.id,
                name=tc.name,
                arguments=tc.arguments,
                result=tool_result_value,
                is_error=is_error,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))
            messages.append(Message(role="tool", content=tr))

    if not final_reached and not trace.error:
        trace.error = f"Max turns ({MAX_TURNS}) exhausted without final output"

    return trace


def run_and_save(
    scenario_id: str,
    customer_id: str,
    customer_message: str,
    agent_provider: Optional[ModelProvider] = None,
) -> Tuple[Trace, Path]:
    """Run a scenario and write the trace to disk."""
    trace = run_scenario(scenario_id, customer_id, customer_message, agent_provider)
    path = write_trace(trace, TRACES_DIR)
    return trace, path
