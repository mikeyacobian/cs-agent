"""Provider factory and exports.

The harness and graders import ONLY from this module. Vendor-specific
SDK classes (Anthropic, OpenAI) are never imported outside this package.
That isolation is the whole point of the abstraction.

Env vars controlling provider selection:
    AGENT_PROVIDER, AGENT_MODEL (defaults: openai, gpt-4o-mini)
    JUDGE_PROVIDER, JUDGE_MODEL (defaults: openai, gpt-4o)

API keys are read by each provider's SDK from the environment at
construction time. The factory only validates that the required key is
set; it does not handle the key value directly.
"""

from __future__ import annotations

import os
from typing import Literal

from harness.providers.base import (
    GenerationResult,
    Message,
    ModelProvider,
    ToolCall,
    ToolResult,
    ToolSpec,
)

Role = Literal["agent", "judge"]


def create_provider(role: Role) -> ModelProvider:
    """Build a ModelProvider for the given role.

    Reads {ROLE}_PROVIDER and {ROLE}_MODEL from env. Falls back to
    sensible defaults for each role.
    """
    role_upper = role.upper()
    provider_id = os.environ.get(f"{role_upper}_PROVIDER", "openai").lower()
    model = os.environ.get(f"{role_upper}_MODEL", _default_model(provider_id, role))

    if provider_id == "openai":
        _require_key("OPENAI_API_KEY", provider_id)
        from harness.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(model=model)
    if provider_id == "claude":
        _require_key("ANTHROPIC_API_KEY", provider_id)
        from harness.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(model=model)
    if provider_id == "mock":
        from harness.providers.mock_provider import MockProvider
        return MockProvider(model=model)
    raise ValueError(
        f"Unknown provider '{provider_id}' for role '{role}'. "
        f"Expected one of: openai, claude, mock."
    )


def _default_model(provider_id: str, role: Role) -> str:
    if provider_id == "openai":
        return "gpt-4o-mini" if role == "agent" else "gpt-4o"
    if provider_id == "claude":
        return "claude-sonnet-4-6"
    return "mock-v1"


def _require_key(key: str, provider_id: str) -> None:
    if not os.environ.get(key):
        raise RuntimeError(
            f"{key} is not set, but provider '{provider_id}' requires it. "
            f"Copy .env.example to .env and fill in the key, or set "
            f"{provider_id.upper()}_PROVIDER=mock to run without keys."
        )


__all__ = [
    "create_provider",
    "Role",
    "ModelProvider",
    "GenerationResult",
    "Message",
    "ToolCall",
    "ToolResult",
    "ToolSpec",
]
