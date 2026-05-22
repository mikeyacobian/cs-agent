"""Model-based grader: LLM-as-judge for customer_response quality.

Uses the JUDGE_PROVIDER (configurable, defaults to a different vendor
than AGENT_PROVIDER for cross-model judging where credentials allow).

The judge reads the customer_response_criteria from the scenario YAML,
the agent's customer_response, and returns a structured verdict.

Why model-based here: empathy, clarity, commitment, and absence of
hostage-style language are not deterministically detectable. They are
exactly what an LLM judge is good at, and exactly the case where the
code-based grader cannot help.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from evals.graders import GraderResult
from harness.providers import create_provider
from harness.providers.base import Message, ModelProvider
from harness.trace import Trace


_JUDGE_SYSTEM_PROMPT = """\
You are an evaluation judge for a customer service agent.

You will be given:
- The customer's original message.
- The agent's customer-facing response.
- A set of criteria the response must satisfy.

Your job is to decide whether the response satisfies the criteria.

Return ONLY a JSON object with this exact shape:
{
  "passed": <true | false>,
  "score": <number between 0.0 and 1.0>,
  "explanation": "<one short paragraph explaining the verdict>"
}

Do not return any other text. Do not return markdown code fences.
"""


def grade_customer_response(
    scenario: Dict[str, Any],
    trace: Trace,
    judge: Optional[ModelProvider] = None,
) -> GraderResult:
    """Evaluate the agent's customer_response against the scenario's criteria."""

    final = trace.final_output
    if not final:
        return GraderResult(
            grader_name="customer_response_quality",
            passed=False,
            score=0.0,
            explanation="No final output produced; cannot evaluate response.",
        )

    customer_response = final.get("customer_response", "")
    criteria = scenario["expected"].get("customer_response_criteria", "")
    customer_message = scenario["input"]["customer_message"]

    judge_input = (
        f"Customer's original message:\n"
        f"{customer_message}\n\n"
        f"Agent's customer-facing response:\n"
        f"{customer_response}\n\n"
        f"Criteria the response must satisfy:\n"
        f"{criteria}\n"
    )

    judge_provider = judge or create_provider("judge")
    result = judge_provider.generate(
        system=_JUDGE_SYSTEM_PROMPT,
        messages=[Message(role="user", content=judge_input)],
        tools=[],
        max_tokens=500,
        temperature=0.1,
    )

    try:
        verdict = json.loads(result.text or "{}")
    except json.JSONDecodeError as e:
        return GraderResult(
            grader_name="customer_response_quality",
            passed=False,
            score=0.0,
            explanation=f"Judge returned invalid JSON: {e}. Raw: {result.text!r}",
        )

    passed = bool(verdict.get("passed", False))
    score = float(verdict.get("score", 0.0))
    explanation = str(verdict.get("explanation", "(no explanation)"))

    return GraderResult(
        grader_name="customer_response_quality",
        passed=passed,
        score=score,
        explanation=explanation,
        expected=criteria,
        actual=customer_response,
    )
