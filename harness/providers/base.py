"""Provider interface: the contract every model provider conforms to.

The harness and graders import only from this module. Vendor SDKs are
imported only inside specific provider implementations (openai.py,
anthropic.py, mock.py). This isolation is the whole point of the
abstraction: no vendor name appears outside `harness/providers/`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class ToolCall:
    """A tool invocation requested by the model.

    `id` is the provider's call identifier (used to match tool results
    back to the call when streaming the conversation forward).
    """

    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """The result of executing a tool call. Appended to the conversation
    so the model can read it on the next turn.
    """

    call_id: str
    name: str
    result: Any
    is_error: bool = False


@dataclass
class GenerationResult:
    """One model response.

    A response is either *final* (no more tool calls; `text` contains the
    structured output as a JSON string) or *tool_calls* (the model wants
    the harness to execute tools and call back).
    """

    text: Optional[str]
    tool_calls: List[ToolCall] = field(default_factory=list)
    stop_reason: str = ""
    model: str = ""
    provider: str = ""
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    raw: Any = None

    @property
    def is_final(self) -> bool:
        """A response is final when the model produced text and did not
        request any more tool calls."""
        return not self.tool_calls and self.text is not None


@dataclass
class Message:
    """A normalized conversation message.

    The harness operates on this normalized shape. Each provider
    translates between this and its own SDK's message format internally.
    """

    role: str  # "system" | "user" | "assistant" | "tool"
    content: Any  # str for user/system/assistant text; ToolResult for tool messages; mixed for assistant tool_use turns
    tool_calls: List[ToolCall] = field(default_factory=list)


@dataclass
class ToolSpec:
    """Tool definition the harness exposes to providers.

    `parameters` is a JSON Schema dict describing the tool's arguments.
    Each provider translates this into its own tool-definition format.
    """

    name: str
    description: str
    parameters: Dict[str, Any]


class ModelProvider(Protocol):
    """Every provider implements this contract.

    The harness never calls anything outside this Protocol. Vendor-
    specific behavior lives entirely inside the implementation file.
    """

    name: str
    model: str

    def generate(
        self,
        system: str,
        messages: List[Message],
        tools: List[ToolSpec],
        output_schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> GenerationResult:
        """Generate one model response.

        Args:
            system: System prompt (loaded from `agent/system_prompt.md`).
            messages: Normalized conversation so far.
            tools: Tool specifications the model may call.
            output_schema: Optional JSON Schema constraining the final
                (non-tool-call) response. Providers that support strict
                JSON output enforce it; providers that do not best-effort.
            max_tokens: Cap on output tokens.
            temperature: Sampling temperature.

        Returns:
            A GenerationResult representing one model turn.
        """
        ...
