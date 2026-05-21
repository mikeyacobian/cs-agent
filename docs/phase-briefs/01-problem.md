# Phase 1 Brief: Problem Definition

This is the mentor prompt for Phase 1. The artifact you produce: [product/01-problem.md](../../product/01-problem.md).

## What Phase 1 is for

Phase 1 defines THE PROBLEM in customer language, anchored in evidence. The artifact is judged by:

- **Specificity** (not "CS is bad")
- **Customer framing** (not "we need to build X")
- **Evidence** (real sources, not invented)
- **Clarity** (a reader who knows nothing about Connectifi can understand it in 3 minutes)

If Phase 1 is mushy, every downstream artifact will be mushy. This is the foundation.

## The artifact's sections, with mentor prompts

### 1. The Problem (One Sentence)

A single sentence in customer language. The sentence should:
- Describe what happens to the customer, not what we're building
- Be specific enough to disagree with
- Avoid corporate framing ("legacy systems," "process gaps") in favor of human language

Bad: "Connectifi has gaps in customer service that need addressing."
Good: "Connectifi customers spend an average of [X] hours and [Y] transfers to resolve routine billing disputes, often giving up before resolution."

**Mentor questions:**
- Could a customer themselves agree with your sentence as a description of their experience?
- Is it specific enough that someone could disagree with it?
- Does it describe what happens, not what we're going to build?

### 2. Who Has This Problem

Define 1-3 specific personas. For each:
- Who they are (account type, tenure, situation)
- What they have in common with other personas
- What's distinct about their version of the pain

Don't say "customers." Say "subscribers trying to cancel after a price increase" or "new customers disputing first-bill charges" or "customers reporting an outage that's already on Connectifi's status page."

**Mentor questions:**
- Are your personas distinct enough that they'd hire different solutions?
- Are you describing real situations, or generic user types?
- Which persona feels the pain most acutely?

### 3. Job-to-be-Done

JTBD format: "When [situation], I want to [motivation], so I can [outcome]."

The agent is the solution. The JTBD is what the customer hires the solution FOR. Get this right and the agent's scope becomes obvious.

**Mentor questions:**
- Is the outcome an emotional one (relief, certainty, control) or a functional one (refund issued, ticket closed)? Best JTBDs include both.
- Are you confusing the JTBD with a feature? "I want a chatbot" is not a JTBD; "I want to fix my bill without re-explaining it three times" is.

### 4. Pain Today (with Evidence)

Specific failure modes with citations. Required sources include at least three of:
- ACSI (American Customer Satisfaction Index) telecom rankings
- JD Power ISP studies
- Consumer Reports
- Academic studies on call center effectiveness
- Your personal experience with Comcast (flag as personal: "Author personal experience with Comcast, [year], [issue]")

Each failure mode should be one paragraph: what happens, why it happens, evidence it happens at scale.

**Mentor questions:**
- For each failure mode, can you point to a source that says it's a real industry pattern, not just your one bad experience?
- Are you mixing personal anecdote with industry research? It is fine to use both; the reader needs to be able to tell which is which.
- Is there a failure mode you think is real but can't source? Flag it as "anecdotal" rather than dropping it.

### 5. Why It Matters

Two dimensions of cost:
- **Human cost**: time, frustration, eventual churn
- **Business cost**: customer acquisition cost wasted, brand damage, churn lifetime value

If you can find real numbers (industry average churn rate, average cost of a CS call, industry NPS), cite them.

**Mentor questions:**
- Have you put a number on either dimension?
- Is the business cost framed as something a CFO would care about (revenue) or only an operations metric (call volume)?

### 6. What "Solved" Looks Like

Describe the customer experience post-solution. NOT a feature list. NOT "an AI agent that..."

"A customer with a billing dispute resolves it in a single interaction. The agent either fixes it on the spot or escalates with a clear timeline. No transfers, no re-explaining, no policy gates."

**Mentor questions:**
- Could you describe this without using the word "agent"?
- Does it describe the customer's experience, or the company's process?

### 7. Why This, Why Now

What changed? The honest answer:
- AI agents are now capable enough to handle structured CS interactions reliably
- Customer expectations have shifted (post-Apple, post-Amazon, post-Chewy)
- The existing CS model is widely documented as broken
- Recent regulatory pressure on ISP cancellation flows (e.g., FTC click-to-cancel rules) creates new urgency

Be careful not to lean on "AI is hot." Lean on specifically what AI can now do that it couldn't 18 months ago.

**Mentor questions:**
- What's the strongest "why now" argument? Lead with that.
- Are you describing inevitability or opportunity? Both work; pick one.

### 8. Sources

Public links, studies, references. Portfolio readers will check these.

### 9. Open Questions for Phase 2

What you don't yet know that discovery should answer. Signal to readers: you know what you don't know.

Examples:
- Industry benchmark for first-call resolution rate
- Whether Connectifi's failure modes are uniform across segments or differ by tenure
- What CS interactions are NOT amenable to agent handling

## How to know Phase 1 is done

Before moving to Phase 2, the artifact passes these checks:

- [ ] The one-sentence problem is specific enough that someone could disagree with it
- [ ] At least 3 cited sources beyond personal experience
- [ ] Personas are differentiated, not generic "customers"
- [ ] "What solved looks like" describes experience, not features
- [ ] A new reader could read it in 5 minutes and explain the problem back
- [ ] No em dashes, no labeled openers
- [ ] No references to prior employment, private projects, or internal company context

## Time estimate

45-90 minutes of focused writing. Probably split over two sittings.

## When you have drafted

Tell me. I will redline against the checks above, push on weakness, and we will iterate.
