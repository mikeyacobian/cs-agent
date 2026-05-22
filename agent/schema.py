"""Output schema for the cs-agent.

The agent produces a structured response conforming to AgentOutput.
This schema is used:
- as the JSON schema for OpenAI structured output (strict mode)
- as the validation target for parsing Claude / Mock responses
- as the contract that graders check against

Six fields, each load-bearing. See DESIGN.md section 6 for rationale.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class IssueType(str, Enum):
    """Classification of the customer's issue. Drives policy lookup."""

    OUTAGE_OR_DEGRADATION = "outage_or_degradation"
    BILLING_DISPUTE = "billing_dispute"
    ACCOUNT_CHANGE = "account_change"
    TECHNICAL_TROUBLESHOOTING = "technical_troubleshooting"
    OTHER = "other"


class RecommendedAction(str, Enum):
    """The pre-routed resolution path the agent picked.

    Each value maps to a pre-committed FI-CAST resolution pathway.
    The agent navigates between these; it does not invent new paths.
    """

    RESOLVE_INLINE = "resolve_inline"
    APPLY_CREDIT = "apply_credit"
    DEFER_TO_OUTAGE_STATUS = "defer_to_outage_status"
    SCHEDULE_CALLBACK = "schedule_callback"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    DECLINE_PER_POLICY = "decline_per_policy"
    REQUEST_MORE_INFO = "request_more_info"


class Evidence(BaseModel):
    """One piece of evidence supporting the agent's recommendation.

    Structured rather than free text so graders can mechanically verify:
    every policy-gated write action must have at least one Evidence entry
    with a populated policy_id matching a policy returned by lookup_policy
    in the trace.
    """

    tool: str = Field(
        ...,
        description="Which tool surfaced this evidence (e.g. 'check_active_incidents').",
    )
    finding: str = Field(
        ...,
        description="One-line summary of what the tool returned that supports the recommendation.",
    )
    policy_id: Optional[str] = Field(
        None,
        description=(
            "Required if this evidence supports a policy-gated write action "
            "(apply_credit, schedule_callback, send_message). Must match a "
            "policy id returned by lookup_policy in the trace."
        ),
    )


class AgentOutput(BaseModel):
    """The structured response the agent produces for every interaction.

    Every field is load-bearing. See DESIGN.md section 6 for full rationale.
    """

    issue_type: IssueType = Field(
        ...,
        description="Classification of the customer's reported issue.",
    )
    recommended_action: RecommendedAction = Field(
        ...,
        description="The pre-routed FI-CAST path the agent picked for this case.",
    )
    customer_response: str = Field(
        ...,
        min_length=1,
        description=(
            "What the customer is told inline in this turn. Empathetic, clear, "
            "committed (timeline if applicable). The customer should never be "
            "asked to re-explain."
        ),
    )
    internal_summary: str = Field(
        ...,
        min_length=1,
        description=(
            "Handoff brief for whoever picks this up next (specialist, "
            "supervisor, or a future agent turn). Sufficient context to act "
            "without re-engaging the customer."
        ),
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Honest calibration of certainty in the chosen action. "
            "Low confidence routes to escalation; high confidence supports "
            "inline resolution."
        ),
    )
    evidence: List[Evidence] = Field(
        ...,
        min_length=1,
        description=(
            "Citations from the trace that support the recommendation. "
            "At least one entry required. For policy-gated write actions, "
            "at least one entry must have a populated policy_id."
        ),
    )

    model_config = {
        "extra": "forbid",
        "use_enum_values": True,
    }
