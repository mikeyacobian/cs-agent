"""Evals layer: graders, scenarios, report builder.

Graders consume traces (produced by the harness) and check them against
scenario expectations. Five code-based graders cover the deterministic
checks; one model-based grader (LLM-as-judge) evaluates customer-facing
language quality.

See `DESIGN.md` section 6 for which schema fields each grader checks,
and section 7 for the per-scenario expectations the graders use.
"""

from evals.graders.code_based import (
    grade_issue_type,
    grade_recommended_action,
    grade_required_tools,
    grade_policy_citations,
    grade_credit_amount,
)
from evals.graders.model_based import grade_customer_response
from evals.runner import evaluate_all, evaluate_scenario

__all__ = [
    "grade_issue_type",
    "grade_recommended_action",
    "grade_required_tools",
    "grade_policy_citations",
    "grade_credit_amount",
    "grade_customer_response",
    "evaluate_all",
    "evaluate_scenario",
]
