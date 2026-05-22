"""Code-based graders.

Five deterministic checks against a trace. Each maps to a specific schema
field or invariant the agent must satisfy.

These are FAST and CHEAP. No API calls, no model invocations. Pure
inspection of the trace's final_output and tool_invocations.

See DESIGN.md section 6 for the full mapping of graders to schema fields.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from evals.graders import GraderResult
from harness.trace import Trace


def _final(trace: Trace) -> Optional[Dict[str, Any]]:
    return trace.final_output


def _called_tools(trace: Trace) -> Set[str]:
    return {ti.name for ti in trace.tool_invocations}


def _cited_policy_ids(trace: Trace) -> Set[str]:
    """All policy_id values appearing in the final output's evidence."""
    final = _final(trace)
    if not final:
        return set()
    evidence = final.get("evidence", [])
    return {
        e.get("policy_id")
        for e in evidence
        if isinstance(e, dict) and e.get("policy_id")
    }


def grade_issue_type(scenario: Dict[str, Any], trace: Trace) -> GraderResult:
    """Did the agent classify the issue correctly?"""
    expected = scenario["expected"]["issue_type"]
    final = _final(trace)
    actual = final.get("issue_type") if final else None
    passed = actual == expected
    return GraderResult(
        grader_name="issue_type_match",
        passed=passed,
        score=1.0 if passed else 0.0,
        explanation=(
            f"Expected '{expected}', got '{actual}'."
            if not passed
            else f"Correctly classified as '{expected}'."
        ),
        expected=expected,
        actual=actual,
    )


def grade_recommended_action(scenario: Dict[str, Any], trace: Trace) -> GraderResult:
    """Did the agent pick the right resolution path?"""
    expected = scenario["expected"]["recommended_action"]
    final = _final(trace)
    actual = final.get("recommended_action") if final else None
    passed = actual == expected
    return GraderResult(
        grader_name="recommended_action_match",
        passed=passed,
        score=1.0 if passed else 0.0,
        explanation=(
            f"Expected '{expected}', got '{actual}'."
            if not passed
            else f"Correctly recommended '{expected}'."
        ),
        expected=expected,
        actual=actual,
    )


def grade_required_tools(scenario: Dict[str, Any], trace: Trace) -> GraderResult:
    """Did the agent call all required read and write tools?"""
    expected_reads: List[str] = scenario["expected"].get("required_read_tools", []) or []
    expected_writes: List[str] = scenario["expected"].get("required_write_tools", []) or []
    required = set(expected_reads) | set(expected_writes)
    called = _called_tools(trace)
    missing = required - called

    passed = len(missing) == 0
    score = 1.0 if passed else max(0.0, 1.0 - (len(missing) / max(len(required), 1)))
    if passed:
        explanation = f"All {len(required)} required tools were called: {sorted(required)}."
    else:
        explanation = (
            f"Missing required tools: {sorted(missing)}. "
            f"Required: {sorted(required)}. Called: {sorted(called)}."
        )
    return GraderResult(
        grader_name="required_tools_called",
        passed=passed,
        score=score,
        explanation=explanation,
        expected=sorted(required),
        actual=sorted(called),
    )


def grade_policy_citations(scenario: Dict[str, Any], trace: Trace) -> GraderResult:
    """Are all required policy citations present in the evidence?"""
    required: List[str] = scenario["expected"].get("required_evidence_policies", []) or []
    cited = _cited_policy_ids(trace)
    missing = set(required) - cited

    passed = len(missing) == 0
    score = 1.0 if passed else max(0.0, 1.0 - (len(missing) / max(len(required), 1)))
    if not required:
        return GraderResult(
            grader_name="policy_citations_complete",
            passed=True,
            score=1.0,
            explanation="No policy citations required for this scenario.",
            skipped=True,
        )
    if passed:
        explanation = f"All required policies cited: {sorted(required)}."
    else:
        explanation = (
            f"Missing policy citations: {sorted(missing)}. "
            f"Required: {sorted(required)}. Cited: {sorted(cited)}."
        )
    return GraderResult(
        grader_name="policy_citations_complete",
        passed=passed,
        score=score,
        explanation=explanation,
        expected=sorted(required),
        actual=sorted(cited),
    )


def grade_credit_amount(scenario: Dict[str, Any], trace: Trace) -> GraderResult:
    """For scenarios with a locked-in expected credit amount, verify the
    actual apply_credit call's amount matches.

    Skipped for scenarios that do not specify expected_credit_amount.
    """
    expected = scenario["expected"].get("expected_credit_amount")
    if expected is None:
        return GraderResult(
            grader_name="credit_amount_correct",
            passed=True,
            score=1.0,
            explanation="No expected credit amount for this scenario.",
            skipped=True,
        )

    apply_credit_calls = [
        ti for ti in trace.tool_invocations if ti.name == "apply_credit"
    ]
    if not apply_credit_calls:
        return GraderResult(
            grader_name="credit_amount_correct",
            passed=False,
            score=0.0,
            explanation=f"Expected credit of ${expected}, but apply_credit was never called.",
            expected=expected,
            actual=None,
        )

    actual_amounts = [ti.arguments.get("amount") for ti in apply_credit_calls]
    if expected in actual_amounts:
        return GraderResult(
            grader_name="credit_amount_correct",
            passed=True,
            score=1.0,
            explanation=f"Applied credit of ${expected} per policy formula.",
            expected=expected,
            actual=actual_amounts,
        )
    return GraderResult(
        grader_name="credit_amount_correct",
        passed=False,
        score=0.0,
        explanation=(
            f"Expected credit of ${expected}, but apply_credit was called with "
            f"{actual_amounts}. (Over: exceeds policy. Under: shortchanges the customer.)"
        ),
        expected=expected,
        actual=actual_amounts,
    )
