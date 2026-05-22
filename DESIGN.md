# DESIGN.md — cs-agent

> Design diary for the 2-hour build. Written live as decisions are made.
> Audience: a reviewer who clones this repo and reads it cold.

## 1. The customer pain

FI-CAST customers carry the labor of resolving service problems they did not cause, looping through unsophisticated automation that escalates badly.

The pain is not the outage. The pain is the work that follows: re-explaining the problem on every transfer, walking through scripted troubleshooting that ignores what the customer already tried, fighting bots that loop instead of resolving. By the time a competent human is reached, if one is reached, the customer is already considering churn.

**Author personal experience (flagged):** Post-outage degraded service from a major ISP, multiple hours across phone and chatbot, both AI-driven, both unsophisticated, repeated negative loops, escalation paths that did not help. Churn risk realized at the customer level.

**The interaction itself is fragile.** Customers must remain tethered to the phone or keep a chat window open. Any disconnection means starting over from zero. Whether this is intentional design (a churn-inducing friction pattern) or accidental, the effect is the same: it amplifies *Hostage-Style Retention*. The customer abandons the attempt and either pays the cost or churns. A CS agent that respects the customer must be resumable; the session state belongs to the customer, not to the channel.

**Industry patterns this touches** (from public-research synthesis, see `docs/research-notes/`):

- *Deflection Wall*: IVR and chatbot systems prioritize call containment over resolution
- *Siloed Context*: every channel transfer erases history; the customer re-explains
- *Blind Script Bondage*: front-line agents (human or AI) follow rigid checklists regardless of customer signal
- *Hostage-Style Retention*: when customers signal churn, the system escalates friction rather than addressing root cause. This includes session fragility (forced tethering, no resumption on disconnect) as a friction-amplifier.

**Why this framing matters for the agent design:** The current state of customer-service AI is part of the pain, not the solution. The product opportunity is not "add AI to CS." It is "build an AI that does not behave like the bots customers already hate."

## 2. Non-goals

These are the scope cuts. Each is anchored to a named alternative or a clear boundary so a reviewer reads deliberate choice rather than gap.

- **Not an Intercom-style chat widget.** This agent decides next-best-action and produces structured output; it is not a conversational support bot bolted into a webpage.
- **Not scoped to a single deflection case.** Single-ticket-type demos prove a narrow point. This agent reasons across multiple issue types.
- **Not a general-purpose coding agent.** Pi and Claude Code cover that space.
- **Not a production-grade agent runtime.** The Claude Agent SDK exists for Claude-only production. We built our own to demonstrate the layer and to support multi-provider with integrated evals.
- **Not a comprehensive eval framework.** Braintrust, LangSmith, Phoenix, Inspect AI exist for this. We built the minimum needed to demonstrate eval-driven development.
- **Not a production CS agent.** Tools are mocked, data is fake, no production systems are integrated, no protected customer information is in play.
- **Not redesigning FI-CAST's operations or escalation authority.** The agent navigates existing pathways; it does not create new ones. Proactive notification, communications authority, and operational changes are out of scope.
- **Not more than three providers.** OpenAI, Claude, Mock. The abstraction supports more; the demo ships three.
- **Not statistical-grade evaluation.** Small-N pass/fail per grader. No power analysis, no paired-difference testing.
- **Not a UI.** Command-line interface plus markdown reports. A minimal UI is a stretch goal only if time permits at the very end.

**What we ARE building, in one sentence:** A hand-rolled multi-provider harness with a scoped read-only triage agent and integrated code-based and model-based evals, sized to the minimum needed to demonstrate eval-driven agent development.

## 3. Purpose

**The agent gets the customer to FI-CAST's existing resolution with as little of their work as possible.** We do not redesign FI-CAST's CS operations or invent new resolution paths. We navigate the ones that exist, correctly, the first time, with the customer carrying none of the navigation labor.

The yardstick is what Amazon and similar companies do well: zero-friction routing for the customer, and when human escalation is needed, the human picks up with complete context. The agent's authority is to act within policy and to recommend (with an auditable handoff) outside it.

**The experiential goal:** when a customer reports an issue, the agent's response is *"it is already resolved,"* or *"we are already on it,"* or *"here is what we are going to do."* Instant competence within a single interaction. The customer is not asked to escalate, re-explain, or chase. The agent's policy-gated write authority is what makes "already resolved" possible. The read-first discipline is what makes "already on it" credible. The handoff orchestration (callback scheduled, specialist cued, case communicated) is what makes "here is what we are going to do" a commitment, not a deflection.

## 4. Operating principles

Five principles that shape every downstream design choice. Each maps directly to a tool, a schema field, a system-prompt line, and a grader.

1. **Customer effort is the cost we minimize, in every path.** Whether the outcome is inline resolution or escalation, the agent does the customer's work: identifying the issue, finding policy, cueing the right specialist, scheduling the callback, communicating the commitment. The customer should never re-explain, re-navigate, or chase.

2. **The agent acts within policy and recommends outside it.** Within policy authorization, the agent takes action directly (apply credit, schedule callback, send message). Outside policy, the agent escalates with full context. Every write action cites the policy that authorizes it. We do not invent new resolution paths or grant the agent discretion beyond policy.

3. **Read context before asking the customer.** Status pages, policy, billing, account state are all available to the agent. If we already know an outage is active, we say so. If policy applies, we cite it. The customer should never be asked to prove something we already know.

4. **Every recommendation cites evidence.** No bare claims. The tool results that support the recommendation are part of the output.

5. **Confidence is honest, not a hedge.** Low confidence means say so and route accordingly. Honest "I don't know" is better than confident wrong.

## 5. Tool surface

The agent has eight tools. Five read tools establish context; three write tools enable policy-gated action. Names reflect what the agent uses them for, not the raw queries underneath. Each tool's return arrives with context, not raw data.

### Read tools (5)

| Tool | Returns | Serves principle |
|---|---|---|
| `lookup_customer(customer_id)` | Identity, tenure, plan, current account status, recent interactions | 1, 3 |
| `get_billing_history(customer_id, months=3)` | Recent billing events with explanations of each charge | 3, 4 |
| `check_active_incidents(region)` | Current outages or service incidents in the customer's region, with ETA where known | 3 |
| `lookup_policy(issue_type)` | Applicable policy text, citable rule, and `authorized_actions` (what the agent may do under this policy, with caps where relevant) | 2, 4 |
| `get_escalation_path(issue_type, severity)` | Who to escalate to, the criteria that trigger escalation, and the expected callback SLA | 2 |

### Write tools (3), all policy-gated

| Tool | Action | Serves principle |
|---|---|---|
| `apply_credit(customer_id, amount, policy_id)` | Apply a service credit. Requires a policy that authorizes credit up to `amount`. Mocked: logs `[mock] applied credit of $X to account Y per policy Z`. | 1, 2 |
| `schedule_callback(customer_id, window, reason, policy_id)` | Schedule a callback in the named time window. Used both for in-scope resolution paths AND for escalation handoffs. Mocked: logs `[mock] scheduled callback for account Y in window W per policy Z`. | 1, 2 |
| `send_message(customer_id, template_id, params, policy_id)` | Send a templated customer-facing message (case-number confirmation, ETA update, resolution notice). Mocked: logs `[mock] sent message <template> to account Y per policy Z`. | 1, 2 |

### Design rules baked into this surface

- **No write tool can be called without a `policy_id` parameter.** The harness validates that the policy authorizes the action and the parameters. The agent's reasoning must include the policy in `evidence`.
- **Write side-effects are mocked.** No actual state mutation. The harness logs the would-be action in the trace. Mocking keeps the eval clean and the demo safe.
- **The communication channel is dual.** `send_message` is the asynchronous customer-facing channel (email, SMS, case-system notice); the structured output's `customer_response` field is what the orchestrator renders inline in the current interaction. Both are populated when both are appropriate.
- **Escalation is fully orchestrated.** When the agent escalates, it cues the specialist via `internal_summary`, schedules the callback via `schedule_callback`, and sends the customer the commitment via `send_message`. The customer leaves the interaction with a case number, a named owner, and a timeline. They never have to chase.

### Out of scope (called out explicitly)

**Layer 2 discretion: agent acting beyond policy.** The agent never exceeds policy authorization. Reasons: consistency (discretion creates fairness problems across customers), auditability (every action must be policy-citable for safety and review), scope discipline (Layer 2 is a separate product decision requiring policy framework redesign). The architecture leaves room for it; this build does not exercise it.

## 6. Output schema

The agent produces a structured response that every grader checks against. Six fields, each with a single load-bearing purpose. See `agent/schema.py` for the Pydantic implementation.

### The six fields

| Field | Type | Purpose |
|---|---|---|
| `issue_type` | enum (5 values) | Classification. Drives policy lookup. |
| `recommended_action` | enum (7 values) | The pre-routed path the agent picked. |
| `customer_response` | string | What the customer is told inline in this turn. |
| `internal_summary` | string | Handoff brief for whoever picks up next. |
| `confidence` | float `0.0` to `1.0` | Calibrated certainty in the action. |
| `evidence` | list of `Evidence` | Citations from the trace. |

### The two enums

**`issue_type`** (5 values):

- `outage_or_degradation`: service is impaired
- `billing_dispute`: customer disputes a charge or expects a credit
- `account_change`: cancellation, downgrade, plan change
- `technical_troubleshooting`: modem, wifi, device-side issues
- `other`: agent could not classify; routes to escalation

**`recommended_action`** (7 values):

- `resolve_inline`: agent fully resolved with available info
- `apply_credit`: credit applied per policy
- `defer_to_outage_status`: known incident; redirect to status + service credit per policy
- `schedule_callback`: specialist callback scheduled with full context committed
- `escalate_to_human`: supervisor or specialist needed; path not yet determined
- `decline_per_policy`: policy says no; explained, escalation offered
- `request_more_info`: agent needs more from customer to act

### Evidence structure

```python
class Evidence:
    tool: str          # which tool surfaced this evidence
    finding: str       # one-line summary of what the tool returned that matters
    policy_id: str?    # required if this evidence supports a policy-gated write
```

Structured evidence forces the agent to do citation work. Free text would let the agent get away with vague phrases. Structure forces it to name the tool and the finding. For policy-gated write actions, `policy_id` is required and must match a policy returned by `lookup_policy` earlier in the trace.

### What was cut

`needs_human_review` (bool) was considered and cut. It is derived from `recommended_action in {escalate_to_human, schedule_callback}` or `confidence < threshold`. Adding it created two sources of truth without adding what graders could check. A "quality QA sampling flag" (mark this case for sampled review even though the action was within policy) would be a different and valid concept; out of scope for this build.

### How this maps to "did the agent take the right action?"

The schema is designed so that five of six grading dimensions are code-based:

| Question | Grader type |
|---|---|
| Was `issue_type` correct for the scenario? | Code-based (ground-truth comparison) |
| Was `recommended_action` valid for the issue + evidence? | Code-based (per-scenario expected action) |
| Did the trace's write-tool calls match `recommended_action`? | Code-based (trace consistency) |
| Was every policy-gated action backed by `policy_id` evidence? | Code-based |
| Was `customer_response` empathetic and committed? | Model-based |
| Was `confidence` calibrated? | Statistical, across runs |

Five code-based, one model-based. That ratio is what makes "observable and testable" hold.

## 7. Scenarios

Three scenarios. Each is a principle test: it should fail in a specific, traceable way if the agent does not follow the principles in section 4. Each lives in `evals/scenarios/` as a YAML file with the expected behavior locked in for the graders.

| # | Scenario | Customer says | What it tests |
|---|---|---|---|
| 1 | `outage_with_active_incident` | "My internet has been slow since the power outage last night." | Information primacy (principle 3): the agent reads `check_active_incidents` first and acts on what it found. Policy-gated write: `apply_credit` per outage policy. Communication: `send_message` with case number + ETA. |
| 2 | `cancellation_post_promo` | "My bill went up to $89. I want to cancel my service." | Honest retention (principles 1, 2): the agent surfaces the loyalty discount AND the cancellation path neutrally. `request_more_info` because the customer must choose, not the agent. |
| 3 | `credit_for_past_outage` | "I had no internet for 3 days last month. I want a credit." | Policy-correct calculation (principles 2, 4): the agent verifies the historical outage, applies the policy formula (not more, not less), explains the calculation. |

### What each scenario explicitly tests AGAINST

- **Scenario 1** must NOT walk the customer through troubleshooting, even though that is what bad CS would do. The active incident is verifiable; the resolution is committed.
- **Scenario 2** must NOT pressure-retain, must NOT skip the offer, must NOT apply the discount unilaterally. Both paths are presented; customer chooses.
- **Scenario 3** must NOT trust the customer's "3 days" claim blindly, must NOT refuse the credit. The agent verifies (2 documented days) and applies the policy-correct amount ($20).

### The mock data world

Five files in `data/` describe the closed FI-CAST world that scenarios reference:

- `customers.json`: three customers (C001, C002, C003), one per scenario, with tenure, region, plan, recent interactions
- `incidents.json`: active and historical service incidents by region
- `billing.json`: three months of billing history per customer
- `policies.json`: the policies the agent looks up (outage credit, outage communication, cancellation, loyalty discount)
- `escalation_paths.json`: routing destinations and callback SLAs by issue type

Each scenario YAML references `customer_id` and the harness resolves it through these data files at runtime. The mock data is small, internally consistent, and reads as a coherent miniature FI-CAST.

## 8. Future direction

Two natural extensions of this architecture that did not make the 2-hour build but are the obvious next moves. These are "what we would build next," not "what we left undone."

**Multi-turn via re-engagement (emerges for free).** The agent is single-turn (one structured output per invocation), but multi-turn customer journeys emerge naturally from the case-number pattern. When a customer re-engages about a prior issue, `lookup_customer` surfaces the prior case in `recent_interactions`. The agent reads it as context and continues. The case number IS the state; persistence lives in the customer-side record, not inside the agent. No state machine to build.

**Proactive action before the customer notices the problem.** Principle 3 (read context first) implies that FI-CAST already has the information needed to know a customer has a problem. If we know an outage is active and which customers it affects, we can apply the credit and send the notification *before* the customer reaches out. This is the Amazon pattern: detect the failed delivery, issue the refund, notify the customer. The cost case is direct: a proactive credit is cheaper than the churn risk of a frustrated customer who navigated the failure modes in section 1 of this doc. The agent's reactive architecture (customer message in, structured action out) is the foundation; the proactive layer wraps it with an operations event source (outage detected, customer targeting) and the communications authority to act on those customers' behalf. That operations layer is out of scope for this build by design; the reactive primitives are the prerequisite for it.
