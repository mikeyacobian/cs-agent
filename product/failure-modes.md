# Failure Modes Log

> **Phase 7 (Iterate).** Growing log of failure modes observed during build and eval iteration.
> **Status:** Not started.

Each entry captures a real failure observed during eval iteration: what the agent did wrong, why it matters, what we changed, whether the fix held.

## Format

```
### F00X: Short title

- **Observed**: What the agent did wrong, with verbatim quote where possible.
- **Task**: Which eval task surfaced it.
- **Why it matters**: The downstream consequence for a real customer.
- **Hypothesis**: Why the agent did this.
- **Fix**: What we changed (prompt edit, new rule, new tool, etc.).
- **Verification**: Eval pass rate before and after.
- **Date**: YYYY-MM-DD.
```

---

_No failures logged yet._
