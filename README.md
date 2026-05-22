# cs-agent

An AI customer service triage agent for **Connectifi**, a fictional ISP modeled on documented failure patterns at large ISPs (Comcast, Charter Spectrum, Cox). Built in a 2-hour sprint to demonstrate scoped agent design, observable runtime architecture, and eval-driven development.

> **Status:** In progress. Built in a single 2-hour session per the project brief.

## What this is

Customer service in cable and internet is documented as among the worst in any consumer category (ACSI, JD Power, Consumer Reports). The well-documented failure modes: opaque billing, cancellation gatekeeping, transfer fatigue, scripted troubleshooting that ignores customer signal.

This project asks: given current AI agent capability, can a thoughtfully-scoped customer service triage agent address those failure modes without making them worse? The agent is the deliverable. The eval harness around it is what proves it works.

See [DESIGN.md](./DESIGN.md) for the full design rationale and the choices behind each decision.

## Architecture at a glance

Three peer layers:

- `agent/`: output schema, system prompt, tool contracts. The thing that thinks.
- `harness/`: provider selection, tool dispatch, trace capture. The runtime that wraps the agent.
- `evals/`: code-based and model-based graders, scenarios, report builder. The quality layer.

The agent runs inside the harness in two modes: `run` (single scenario, trace only) and `eval` (full corpus, trace plus graders, report). Both modes produce the same trace schema. Eval mode is `run` mode plus grading.

## How to run

_To be filled in at the end of the build with the actual commands. Expected entry points: `smoke` (no API key required, uses Mock provider), `run --scenario <id>` (real provider, single scenario), `eval` (full corpus + report)._

## On provider abstraction

Every model call (agent and judge) goes through one `ModelProvider` interface with three implementations: OpenAI (real), Mock (real, no API key needed), Claude (stub; production migration path noted in `harness/providers/`). Provider selection via `.env`. The Mock provider exists so the harness can be smoke-tested with zero spend.

## On scope

Built in 2 hours. Explicit non-goals: a general-purpose coding agent (Pi, Claude Code cover this), a production-grade agent runtime (Claude Agent SDK), a comprehensive eval framework (Braintrust, LangSmith, Phoenix), a production CS agent (this is a demo; tools and data are mocked). See [DESIGN.md](./DESIGN.md) for the full non-goals list.

## License

MIT. See [LICENSE](./LICENSE).

## On fiction

Connectifi is fictional. Its CS challenges are modeled on documented patterns at large ISPs per public research and personal experience. No real customer data, employee names, or internal policies appear anywhere in this repo.
