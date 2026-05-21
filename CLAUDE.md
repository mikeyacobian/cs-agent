# cs-agent — Claude session brief

This file orients Claude Code sessions opened on this project. Read at session start.

## What this project is

An AI customer service agent for **Connectifi**, a fictional ISP analog to Comcast/Spectrum/Cox. The project is a portfolio piece demonstrating AI-first product management. Audience: someone evaluating Mike for an AI PM role.

**This is not a learning exercise.** The artifacts are intended to be shareable, public, and held to portfolio quality. No content from prior employment, private projects, or internal company context can leak through.

## The workflow

The project follows an 8-phase PM flow with eval-driven build:

| Phase | Output | Driver |
|---|---|---|
| 1. Problem | `product/01-problem.md` | Mike |
| 2. Discovery | `product/02-discovery.md` | Mike |
| 3. PRD | `product/03-prd.md` | Mike |
| 4. Eval strategy | `product/04-eval-strategy.md` | Mike |
| 5. Design | `product/05-design.md` | Mike |
| 6. Build (2hr sprint) | `agent/`, `evals/`, `data/`, code | Claude to Mike's spec |
| 7. Iterate | `product/failure-modes.md` | Both |
| 8. Launch readout | `product/06-launch.md` | Mike |

Phase briefs live in `docs/phase-briefs/`. Each brief is the mentor prompt for that phase.

## How Claude works in this project

**Phases 1-5 and 8 (Product artifacts): Mike drafts, Claude redlines.**

Mike's voice. Mike's judgment. Mike's reasoning. Claude's job is to:
- Provide structure (phase briefs)
- Ask the questions a strong PM mentor would ask
- Redline drafts against rigor checks
- Surface gaps and weak claims
- Never ghostwrite the artifact itself

If Claude finds itself writing the artifact's substantive content, stop. This is a portfolio piece. Readers can smell ghostwriting. Mike loses if the artifacts aren't his.

**Phase 6 (Build): Claude writes code to Mike's spec.**

Mock data, harness, graders, system prompt, demo CLI. Architecture decisions (output schema, tool surface, escalation taxonomy) are Mike's calls. Implementation is Claude's. Time budget: 2 hours total. See `docs/phase-briefs/06-build-sprint.md` for the per-commit budget when it exists.

**Phase 7 (Iterate): Both.**

Mike reads transcripts, decides what's a real failure, captures patterns. Claude executes prompt edits and re-runs evals.

## Hard rules

- **Nothing from prior employment or private context leaks in.** No internal product names, ticket prefixes, codenames, colleague names, private channels, or internal documentation references from any company or project outside this repo. Patterns transfer; specifics do not.
- **No em dashes anywhere.** Use commas, semicolons, parentheses, or restructure. The rule is non-negotiable.
- **No labeled openers** ("Quick note:", "Heads up:", "Just wanted to..."). Lead with substance.
- **Don't ghostwrite product artifacts.** If Mike asks Claude to "draft the PRD," push back. Claude can draft an outline; Mike fills in reasoning and prose.
- **Cite sources in product artifacts.** Public research only. ACSI, JD Power, Consumer Reports, named industry studies. Personal experience is allowed but must be flagged as such.
- **First-principles eval framework.** Build our own harness in `evals/`. Document in `04-eval-strategy.md` that Inspect/Promptfoo/Braintrust/LangSmith exist and were considered; explain why we built our own for this exercise.
- **Provider abstraction is mandatory.** The harness is provider-agnostic. All model calls go through a single `ModelProvider` interface in `evals/providers/`. Three implementations: Claude, OpenAI, Mock. Provider selection happens via env vars (`AGENT_PROVIDER`, `JUDGE_PROVIDER`), never hardcoded. The default judge is cross-model from the default agent to reduce self-preference bias. See `evals/providers/README.md` for the locked architecture.
- **No vendor names in harness or grader bodies.** Harness and graders import `create_provider` only. They never reference `Anthropic`, `OpenAI`, or any other SDK class directly. If a vendor name appears outside `evals/providers/`, that is a bug.
- **No hardcoded API keys.** Provider code never reads keys from `os.environ` directly; SDK defaults handle that. Keys live in `.env` (gitignored) and are validated at provider construction with clear error messages.

## Project context

- License: MIT (see LICENSE)
- Repo will be pushed to GitHub when Mike is ready; clean commits matter
- Fictional company: Connectifi, fictional ISP, Comcast-analog
- Mike has personal Comcast experience he'll draw from in discovery
- Build sprint is 2 hours, gated on all PM artifacts being locked first
