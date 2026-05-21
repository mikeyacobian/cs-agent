# evals/providers — ModelProvider Abstraction

This directory implements the provider-agnostic model interface used by the eval harness and graders. Architecture is **locked** before build-sprint kickoff so we do not relitigate it under time pressure.

## Why provider abstraction

The eval harness must be portable, testable, and free of vendor lock-in:

- **Portability**: anyone cloning the repo runs it with whatever API credits they have
- **Testing**: a mock provider enables unit tests of grader logic with zero API spend
- **Cross-model judging**: agent and judge can run on different providers to reduce self-preference bias
- **Resilience**: when one provider has an outage, swap to another
- **Portfolio signal**: demonstrates architectural rigor rather than vendor stickiness

There is no scenario in this project where hardcoding a single provider is the right call.

## The contract

`providers/base.py` defines a single interface that every implementation conforms to:

```python
from dataclasses import dataclass
from typing import Protocol, Optional

@dataclass
class GenerationResult:
    text: str
    model: str
    provider: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None

class ModelProvider(Protocol):
    name: str
    model: str
    def generate(
        self,
        system: str,
        user: str,
        max_tokens: int = 2000,
        temperature: float = 1.0,
    ) -> GenerationResult: ...
```

Every implementation returns the same `GenerationResult` shape regardless of provider. Token counts and latency are optional because not every provider exposes them identically.

## Implementations (one file each)

| File | Provider | Notes |
|---|---|---|
| `claude.py` | Anthropic Claude | Wraps `anthropic.Anthropic()`. Reads `ANTHROPIC_API_KEY` via SDK default. |
| `openai.py` | OpenAI | Wraps `openai.OpenAI()`. Reads `OPENAI_API_KEY` via SDK default. |
| `mock.py` | Mock / canned | Takes a `responder` callable; returns deterministic results with zero API spend. |

Each implementation is ~30 lines. The SDK is imported inside the implementation file (not at module top level) so the harness can run with only one SDK installed if desired.

## The factory

`providers/__init__.py` exposes `create_provider(role)` where `role` is `"agent"` or `"judge"`. The factory reads `{ROLE}_PROVIDER` and `{ROLE}_MODEL` env vars and returns the appropriate implementation. It validates that the required API key is set and fails fast with a clear error if not.

```python
provider = create_provider("agent")
result = provider.generate(system=..., user=...)
```

The harness never references `Anthropic`, `OpenAI`, or any other SDK class directly. If a vendor name appears outside `evals/providers/`, that is a bug.

## Configuration

All provider config lives in env vars. See `.env.example` at the repo root.

| Variable | Purpose | Example |
|---|---|---|
| `AGENT_PROVIDER` | Which provider powers the agent under test | `claude` |
| `AGENT_MODEL` | Specific model id within that provider | `claude-sonnet-4-6` |
| `JUDGE_PROVIDER` | Which provider powers the LLM judge | `openai` |
| `JUDGE_MODEL` | Specific model id for the judge | `gpt-4o` |
| `ANTHROPIC_API_KEY` | Required when any provider is `claude` | `sk-ant-...` |
| `OPENAI_API_KEY` | Required when any provider is `openai` | `sk-...` |

Default config is **cross-model**: Claude as agent, OpenAI as judge. This reduces self-preference bias by default. Override at any time via env.

## Per-task overrides (future, not v1)

Task YAMLs can override the default agent/judge for that specific task. Not built in v1; documented here as a known extension point.

```yaml
input:
  system_prompt: ...
  user_message: ...
  agent_provider: openai     # overrides AGENT_PROVIDER for this task only
  agent_model: gpt-4o
```

Use case: comparing agent behavior across providers on the same task corpus.

## Adding a new provider

One new file plus three lines in the factory. The Protocol is the only contract; conform to it and the harness and graders pick up the new provider with zero changes.

## What this enables for testing

The mock provider is the load-bearing piece for harness testing:

```python
from providers.mock import MockProvider

mock = MockProvider(
    responder=lambda system, user: '{"verdict": "pass", "reasoning": "clean"}'
)
# Use this mock as the judge in a unit test; assert grader behavior without API spend.
```

Grader tests run in CI without any API key configured. Real eval runs require real provider credentials.

## Status

Architecture: locked. Implementation: pending build sprint.
