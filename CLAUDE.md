# cs-agent — Claude session brief

This file orients Claude Code sessions on this project. Read at session start.

## What this project is

An AI customer service triage agent for **FI-CAST**, a fictional ISP modeled on documented failure patterns at large ISPs (Comcast, Charter Spectrum, Cox). Portfolio piece for a Lead PM interview. Built in a 2-hour sprint per the hiring manager's prompt. Deliverables: working agent, repo, 5-minute video walkthrough.

The artifacts are intended to be shareable and held to portfolio quality. No content from prior employment, private projects, or internal company context can leak through.

## Build approach

The build runs in **product-led order**: customer pain → agent purpose + principles → tool surface → output schema → scenarios → system prompt → harness → graders → CLI. Each decision earns its place by being derived from the prior one. `DESIGN.md` is the design diary, written live as decisions are made.

## How Claude works in this project

**Product decisions are Mike's.** Scope, principles, tool surface, output schema, scenario picks, system prompt content. Claude asks the question, captures the decision in `DESIGN.md` with one line of rationale, and moves on. Claude does not propose architecture mid-phase or ghostwrite product reasoning.

**Implementation is Claude's.** Once a component spec is locked, Claude writes the code. Mike steers, reviews, adjusts.

If Claude finds itself writing prose that explains Mike's reasoning rather than capturing Mike's words, stop. The artifact has to be Mike's voice.

## Hard rules

- **No content from prior employment or private context.** No internal product names, ticket prefixes, codenames, colleague names, or internal documentation references from any company outside this repo. Patterns transfer; specifics do not.
- **No em dashes anywhere.** Use commas, semicolons, parentheses, or restructure. Non-negotiable.
- **No labeled openers** ("Quick note:", "Heads up:"). Lead with substance.
- **Cite sources in design artifacts.** Public research only (ACSI, JD Power, Consumer Reports, named industry studies). Personal experience allowed but flagged.
- **First-principles harness.** We build our own in `harness/`. `DESIGN.md` notes the Claude Agent SDK and Pi exist and were considered; explains why we built our own.
- **Provider abstraction is mandatory.** All model calls go through one `ModelProvider` interface in `harness/providers/`. Three real implementations: OpenAI, Claude, Mock. Reviewer with either OpenAI or Anthropic credentials can run the full pipeline; Mock enables zero-spend smoke testing.
- **Mock provider exists for zero-spend smoke testing.** The harness must run end to end with no API keys via the Mock provider.
- **No vendor names outside `harness/providers/`.** Code elsewhere never imports `anthropic`, `openai`, or any other SDK class.
- **No hardcoded API keys.** SDK defaults handle key reading; `.env` is gitignored.
- **Agent has policy-gated write authority.** Three write tools (`apply_credit`, `schedule_callback`, `send_message`) require a `policy_id` parameter. The harness validates that the cited policy authorizes the action. Write side-effects are mocked in this build (logged in trace, not persisted). Discretion beyond policy (Layer 2) is out of scope.
- **Anthropic vocabulary in eval terminology.** "Code-based graders" and "model-based graders" (not "deterministic" and "model-graded").

## Architecture

Three layers as peers:

| Layer | Lives in | Responsibility |
|---|---|---|
| Agent | `agent/` | Output schema, system prompt, tool contracts |
| Harness | `harness/` | Runtime: providers, tool dispatch, trace capture |
| Evals | `evals/` | Graders (code-based + model-based), scenarios, report builder |

The agent runs inside the harness. The evals also run inside the harness. The harness has two modes (`run` and `eval`) and produces the same trace schema in both.

## Project context

- License: MIT (see LICENSE)
- Repo will be pushed to GitHub at the end of the build
- Fictional company: FI-CAST (Comcast-analog ISP)
- Provider credits available to the author: OpenAI. Demo uses cross-tier OpenAI (stronger judge grading weaker agent). Cross-vendor judging (Claude judge over OpenAI agent, or vice versa) is shipped as a one-env-var override; reviewers with both keys can flip in seconds.
