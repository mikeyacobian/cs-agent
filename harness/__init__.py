"""Harness layer: runtime that wraps the agent.

The harness owns:
- Provider selection (in harness.providers)
- Tool dispatch (agent.tools registers; harness.runner invokes)
- Trace capture (harness.trace; every run produces a Trace)
- The runner loop (harness.runner; the tool-use loop)

The agent runs inside the harness in two modes (`run`, `eval`). Both
modes produce traces with the same schema. Eval mode is run mode plus
grading.
"""

from harness.providers import (
    GenerationResult,
    Message,
    ModelProvider,
    Role,
    ToolCall,
    ToolResult,
    ToolSpec,
    create_provider,
)
from harness.runner import (
    MAX_TURNS,
    TRACES_DIR,
    load_system_prompt,
    run_and_save,
    run_scenario,
)
from harness.trace import (
    Trace,
    ToolInvocation,
    TurnCall,
    new_trace,
    write_trace,
)

__all__ = [
    "create_provider",
    "run_scenario",
    "run_and_save",
    "load_system_prompt",
    "Trace",
    "ToolInvocation",
    "TurnCall",
    "new_trace",
    "write_trace",
    "ModelProvider",
    "Message",
    "ToolCall",
    "ToolResult",
    "ToolSpec",
    "Role",
    "GenerationResult",
    "MAX_TURNS",
    "TRACES_DIR",
]
