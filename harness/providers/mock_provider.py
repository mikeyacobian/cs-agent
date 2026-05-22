"""Mock provider for smoke testing without API keys.

Returns deterministic responses based on the conversation state. Two-turn
flow per scenario: first turn calls read tools; second turn returns a
canned structured AgentOutput appropriate to the customer message.

Used by:
- The smoke-test entry point to verify the harness runs end to end
- Unit tests of graders and the runner

No API calls, no spend, no key required.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from harness.providers.base import (
    GenerationResult,
    Message,
    ToolCall,
    ToolResult,
    ToolSpec,
)


class MockProvider:
    """Deterministic mock. Two-turn flow per scenario."""

    name = "mock"

    def __init__(self, model: str = "mock-v1"):
        self.model = model
        self._call_count = 0

    def generate(
        self,
        system: str,
        messages: List[Message],
        tools: List[ToolSpec],
        output_schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> GenerationResult:
        self._call_count += 1

        # If no tools are provided, this is a judge invocation: return judge-shaped JSON
        if not tools:
            judge_output = {
                "passed": True,
                "score": 0.85,
                "explanation": "(Mock judge) Response satisfies the stated criteria. Mock judging is not real evaluation; smoke-test only.",
            }
            return GenerationResult(
                text=json.dumps(judge_output),
                tool_calls=[],
                stop_reason="end_turn",
                model=self.model,
                provider=self.name,
                input_tokens=0,
                output_tokens=0,
                latency_ms=1,
                raw=None,
            )

        has_tool_results = any(m.role == "tool" for m in messages)

        if not has_tool_results:
            # First turn: ask for a couple of read tools to demonstrate the flow
            tool_calls = self._first_turn_calls(messages, tools)
            return GenerationResult(
                text=None,
                tool_calls=tool_calls,
                stop_reason="tool_use",
                model=self.model,
                provider=self.name,
                input_tokens=0,
                output_tokens=0,
                latency_ms=1,
                raw=None,
            )

        # Tool results present: return canned structured output
        output = self._canned_output_for(messages)
        return GenerationResult(
            text=json.dumps(output),
            tool_calls=[],
            stop_reason="end_turn",
            model=self.model,
            provider=self.name,
            input_tokens=0,
            output_tokens=0,
            latency_ms=1,
            raw=None,
        )

    def _first_turn_calls(self, messages: List[Message], tools: List[ToolSpec]) -> List[ToolCall]:
        customer_id = self._extract_customer_id(messages) or "C001"
        tool_names = {t.name for t in tools}
        calls: List[ToolCall] = []
        if "lookup_customer" in tool_names:
            calls.append(ToolCall(
                id=f"mock_call_lookup_{self._call_count}",
                name="lookup_customer",
                arguments={"customer_id": customer_id},
            ))
        if "lookup_policy" in tool_names:
            calls.append(ToolCall(
                id=f"mock_call_policy_{self._call_count}",
                name="lookup_policy",
                arguments={"issue_type": "outage_or_degradation"},
            ))
        return calls

    def _canned_output_for(self, messages: List[Message]) -> Dict[str, Any]:
        """Pick a canned output shape based on keywords in the customer message."""
        text = ""
        for m in messages:
            if m.role == "user" and isinstance(m.content, str):
                text += " " + m.content.lower()

        if "cancel" in text:
            return {
                "issue_type": "account_change",
                "recommended_action": "request_more_info",
                "customer_response": (
                    "I understand your bill went up after your promotional rate ended. "
                    "You have two options I can act on right now: a $20/month loyalty "
                    "discount for 6 months given your tenure, or processing the cancellation. "
                    "Which would you like? (Mock provider canned response.)"
                ),
                "internal_summary": (
                    "Mock: cancellation request, both options presented per "
                    "POL-CANCELLATION and POL-LOYALTY-DISCOUNT; awaiting customer choice."
                ),
                "confidence": 0.80,
                "evidence": [
                    {"tool": "lookup_customer", "finding": "Tenure 14 months (loyalty eligible)", "policy_id": None},
                    {"tool": "lookup_policy", "finding": "POL-CANCELLATION + POL-LOYALTY-DISCOUNT apply", "policy_id": "POL-CANCELLATION"},
                ],
            }

        if "credit" in text or "no internet" in text or "days last month" in text:
            return {
                "issue_type": "billing_dispute",
                "recommended_action": "apply_credit",
                "customer_response": (
                    "I see there was a documented outage in your area for 2 days last month "
                    "(INC-78). Per our service credit policy, I have applied a $20 credit to "
                    "your account ($10/day x 2 documented days). You mentioned 3 days; our "
                    "records confirm 2 days. The credit appears on your next bill. "
                    "(Mock provider canned response.)"
                ),
                "internal_summary": (
                    "Mock: applied $20 credit for INC-78 (2 documented days) per "
                    "POL-OUTAGE-CREDIT formula. Customer claim of 3 days addressed."
                ),
                "confidence": 0.88,
                "evidence": [
                    {"tool": "check_active_incidents", "finding": "INC-78 historical outage, 2 documented days", "policy_id": None},
                    {"tool": "lookup_policy", "finding": "$10 per documented outage day, max $50", "policy_id": "POL-OUTAGE-CREDIT"},
                ],
            }

        # Default: active outage scenario
        return {
            "issue_type": "outage_or_degradation",
            "recommended_action": "defer_to_outage_status",
            "customer_response": (
                "I can see there is an active outage in your area, case POW-04, with "
                "restoration expected by tomorrow at 8 AM. I have applied a service credit "
                "per our outage policy. You will receive a confirmation message shortly. "
                "(Mock provider canned response.)"
            ),
            "internal_summary": (
                "Mock: outage POW-04 acknowledged, credit applied per POL-OUTAGE-CREDIT, "
                "customer notified."
            ),
            "confidence": 0.85,
            "evidence": [
                {"tool": "check_active_incidents", "finding": "Active POW-04 outage in customer region", "policy_id": None},
                {"tool": "lookup_policy", "finding": "POL-OUTAGE-CREDIT authorizes service credit", "policy_id": "POL-OUTAGE-CREDIT"},
            ],
        }

    def _extract_customer_id(self, messages: List[Message]) -> Optional[str]:
        for m in messages:
            if m.role == "user" and isinstance(m.content, str):
                for cid in ("C001", "C002", "C003"):
                    if cid in m.content:
                        return cid
        return None
