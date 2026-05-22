# cs-agent

An AI customer service triage agent for **FI-CAST**, a fictional ISP modeled on documented failure patterns at large ISPs (Comcast, Charter Spectrum, Cox). Built in a 2-hour sprint to demonstrate scoped agent design, observable runtime architecture, and eval-driven development.

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

### Install

Requires Python 3.10+.

```bash
git clone https://github.com/mikeyacobian/cs-agent
cd cs-agent
python3.11 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

### Smoke test (no API keys required)

Verifies the harness runs end to end with the Mock provider. Useful as the first thing you run after cloning.

```bash
.venv/bin/python -m cli.main smoke
```

You should see `[smoke] OK: harness end-to-end works.` plus a trace path.

### Configure providers

Copy the example env file and pick the providers/keys you have:

```bash
cp .env.example .env
# edit .env:
#   AGENT_PROVIDER=openai | claude | mock
#   JUDGE_PROVIDER=openai | claude | mock
#   OPENAI_API_KEY=...     (only if any provider above is openai)
#   ANTHROPIC_API_KEY=...  (only if any provider above is claude)
```

Defaults are cross-tier within OpenAI (`gpt-4o` agent, `gpt-5` judge): stronger judge over weaker agent, cross-generation for some self-preference bias mitigation. Mock works with no keys for grader and smoke iteration. Cross-vendor judging (Claude judge over OpenAI agent, or vice versa) is one env var change away.

### Run one scenario

```bash
.venv/bin/python -m cli.main run --scenario outage_with_active_incident
.venv/bin/python -m cli.main run --scenario cancellation_post_promo
.venv/bin/python -m cli.main run --scenario credit_for_past_outage
```

Writes a trace to `traces/` and prints the agent's structured output.

### Full eval

```bash
.venv/bin/python -m cli.main eval
```

Runs every scenario, applies six graders to each, writes a markdown report to `reports/`. Open the report in your editor to see per-scenario pass/fail breakdowns.

## On provider abstraction

Every model call (agent and judge) goes through one `ModelProvider` interface with three real implementations: OpenAI, Claude, and Mock. Provider selection via `.env`. Reviewers with either OpenAI or Anthropic credits can run the full pipeline; the Mock provider lets anyone smoke-test the harness with zero spend.

## On scope

Built in 2 hours. Explicit non-goals: a general-purpose coding agent (Pi, Claude Code cover this), a production-grade agent runtime (Claude Agent SDK), a comprehensive eval framework (Braintrust, LangSmith, Phoenix), a production CS agent (this is a demo; tools and data are mocked). See [DESIGN.md](./DESIGN.md) for the full non-goals list.

## License

MIT. See [LICENSE](./LICENSE).

## On fiction

FI-CAST is fictional. Its CS challenges are modeled on documented patterns at large ISPs per public research and personal experience. No real customer data, employee names, or internal policies appear anywhere in this repo.
