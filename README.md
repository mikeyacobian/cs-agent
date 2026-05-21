# cs-agent

An AI-first customer service agent for **Connectifi**, a fictional ISP modeled on documented failure patterns in the broadband industry.

> **Status: In progress.** This is a portfolio project demonstrating AI-first product management. The work is being built phase-by-phase per the [product workflow](./product/).

## What this is

Customer service in industries like cable/internet is documented as among the worst in any consumer category (ACSI, JD Power, Consumer Reports). The pain points are well known: opaque billing, cancellation gatekeeping, escalation friction, agent authority limits, transfer fatigue.

This project asks: given the current state of AI agents, can a thoughtfully-designed customer service agent address those failure modes without making them worse? The answer requires more than building an agent. It requires a measurement system that proves whether the agent actually solves the problems it claims to.

The agent is the deliverable. The eval suite is what makes it credible.

## Project shape

This project treats agent-building as a product management discipline, not a coding exercise. Each phase produces a real PM artifact.

| Phase | Artifact | Status |
|---|---|---|
| 1. Problem | [product/01-problem.md](./product/01-problem.md) | Not started |
| 2. Discovery | [product/02-discovery.md](./product/02-discovery.md) | Not started |
| 3. PRD | [product/03-prd.md](./product/03-prd.md) | Not started |
| 4. Eval strategy | [product/04-eval-strategy.md](./product/04-eval-strategy.md) | Not started |
| 5. Design | [product/05-design.md](./product/05-design.md) | Not started |
| 6. Build | `agent/`, `evals/`, `data/` | Not started |
| 7. Iterate | [product/failure-modes.md](./product/failure-modes.md) | Not started |
| 8. Launch readout | [product/06-launch.md](./product/06-launch.md) | Not started |

## Repo structure

```
cs-agent/
├── product/             # PM artifacts (problem, discovery, PRD, eval strategy, design, launch)
├── docs/                # Supporting docs, phase briefs, research notes
├── agent/               # System prompt, policy, tools
├── data/                # Mock customer and order data
├── evals/               # Eval harness, graders, task corpus, runs
│   └── providers/       # Provider-agnostic ModelProvider abstraction (Claude, OpenAI, Mock)
└── demo/                # Interactive CLI demo
```

## A note on provider abstraction

The eval harness is provider-agnostic by design. All model calls (both agent-under-test and LLM judge) go through a single `ModelProvider` interface with three implementations: Claude, OpenAI, and Mock. Provider selection is configured via environment variables (`AGENT_PROVIDER`, `JUDGE_PROVIDER`); no vendor name is hardcoded in the harness or graders.

This means:

- The agent and the judge can be on different providers (cross-model judging is the recommended default to reduce self-preference bias)
- Anyone cloning the repo can run it with whatever API credits they have
- A mock provider enables unit testing of grader logic with zero API spend
- Adding a new provider is one new file plus three lines in the factory

See [evals/providers/README.md](./evals/providers/README.md) for the architecture details and [.env.example](./.env.example) for the environment variable structure.

## A note on fiction

Connectifi is fictional. Its CS challenges are modeled on documented patterns at large ISPs (Comcast, Charter Spectrum, Cox) per public research and personal experience. No real customer data, real employee names, or real internal policies appear anywhere in this repo.

## License

MIT. See [LICENSE](./LICENSE).
