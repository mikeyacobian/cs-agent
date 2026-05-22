"""Tool surface for the FI-CAST customer service agent.

Eight tools total:
  - 5 read tools (read-only access to mock data in `data/*.json`)
  - 3 write tools (policy-gated; side effects are mocked)

Each tool has a JSON schema for its parameters. The harness exposes these
specs to whichever provider is in use; the provider translates to its own
tool-definition format.

Read tools load from `data/*.json`. Write tools log their would-be effect
for the trace; no real state mutation, because the agent is read-only in
practice for this build.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from harness.providers.base import ToolSpec

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ---------- Data-loading helpers ----------


def _load_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text())


# ---------- Read tool implementations ----------


def lookup_customer(customer_id: str) -> Dict[str, Any]:
    """Return identity, tenure, plan, account status, and recent interactions."""
    customers = _load_json("customers.json")
    if customer_id not in customers:
        return {"error": f"customer {customer_id} not found"}
    return customers[customer_id]


def get_billing_history(customer_id: str, months: int = 3) -> Dict[str, Any]:
    """Return the customer's recent billing events with explanations."""
    billing = _load_json("billing.json")
    if customer_id not in billing:
        return {"error": f"no billing record for {customer_id}"}
    record = billing[customer_id]
    history = record["last_3_months"]
    if months < 3:
        history = history[-months:]
    return {
        "customer_id": customer_id,
        "history": history,
        "current_balance": record["current_balance"],
    }


def check_active_incidents(region: str, time_window: str = "current") -> Dict[str, Any]:
    """Return active and/or historical service incidents in the given region.

    time_window: 'current' (active only), 'historical' (recent past),
                 or 'all' (both).
    """
    incidents = _load_json("incidents.json")
    results: Dict[str, List[Dict[str, Any]]] = {"active": [], "historical": []}
    if time_window in ("current", "all"):
        results["active"] = [i for i in incidents["active"] if i["region"] == region]
    if time_window in ("historical", "all"):
        results["historical"] = [i for i in incidents["historical"] if i["region"] == region]
    return results


def lookup_policy(issue_type: str) -> Dict[str, Any]:
    """Return all policies applicable to the given issue type."""
    policies = _load_json("policies.json")
    applicable = [
        p for p in policies.values()
        if issue_type in p.get("applicable_issue_types", [])
    ]
    return {"issue_type": issue_type, "policies": applicable}


def get_escalation_path(issue_type: str, severity: str = "normal") -> Dict[str, Any]:
    """Return the specialist queue and callback SLA for an issue type."""
    paths = _load_json("escalation_paths.json")
    path = paths.get(issue_type, paths.get("other", {}))
    return {
        "issue_type": issue_type,
        "severity": severity,
        "queue": path.get("queue"),
        "callback_sla_hours": path.get("callback_sla_hours"),
        "description": path.get("description"),
    }


# ---------- Write tool implementations (policy-gated, mocked) ----------


def apply_credit(customer_id: str, amount: float, policy_id: str) -> Dict[str, Any]:
    """Apply a service credit. Mocked: logs the effect, no state mutation."""
    log = f"[mock] applied credit of ${amount:.2f} to account {customer_id} per policy {policy_id}"
    return {
        "action": "apply_credit",
        "status": "ok",
        "customer_id": customer_id,
        "amount": amount,
        "policy_id": policy_id,
        "log": log,
    }


def schedule_callback(
    customer_id: str,
    window: str,
    reason: str,
    policy_id: str,
) -> Dict[str, Any]:
    """Schedule a callback from a specialist queue. Mocked: logs the effect."""
    log = (
        f"[mock] scheduled callback for account {customer_id} "
        f"in window '{window}' per policy {policy_id}"
    )
    return {
        "action": "schedule_callback",
        "status": "ok",
        "customer_id": customer_id,
        "window": window,
        "reason": reason,
        "policy_id": policy_id,
        "log": log,
    }


def send_message(
    customer_id: str,
    template_id: str,
    params: Optional[Dict[str, Any]] = None,
    policy_id: str = "",
) -> Dict[str, Any]:
    """Send a templated customer message. Mocked: logs the effect."""
    params = params or {}
    log = (
        f"[mock] sent message '{template_id}' to account {customer_id} "
        f"per policy {policy_id}"
    )
    return {
        "action": "send_message",
        "status": "ok",
        "customer_id": customer_id,
        "template_id": template_id,
        "params": params,
        "policy_id": policy_id,
        "log": log,
    }


# ---------- Registry and dispatch ----------


TOOL_IMPLEMENTATIONS: Dict[str, Callable[..., Any]] = {
    "lookup_customer": lookup_customer,
    "get_billing_history": get_billing_history,
    "check_active_incidents": check_active_incidents,
    "lookup_policy": lookup_policy,
    "get_escalation_path": get_escalation_path,
    "apply_credit": apply_credit,
    "schedule_callback": schedule_callback,
    "send_message": send_message,
}


def dispatch(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a tool call. Returns the tool's result, or an error dict."""
    fn = TOOL_IMPLEMENTATIONS.get(tool_name)
    if not fn:
        return {"error": f"unknown tool: {tool_name}"}
    try:
        return fn(**arguments)
    except TypeError as e:
        return {"error": f"bad arguments for {tool_name}: {e}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


# ---------- Tool specs (consumed by providers) ----------


TOOL_SPECS: List[ToolSpec] = [
    ToolSpec(
        name="lookup_customer",
        description=(
            "Look up the customer's identity, tenure, plan, region, account "
            "status, and recent interactions. Call this first to understand "
            "who you are talking to."
        ),
        parameters={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer account ID (e.g. C001)."},
            },
            "required": ["customer_id"],
        },
    ),
    ToolSpec(
        name="get_billing_history",
        description="Return the customer's recent billing events with an explanation per charge.",
        parameters={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "months": {"type": "integer", "description": "Months of history (default 3).", "default": 3},
            },
            "required": ["customer_id"],
        },
    ),
    ToolSpec(
        name="check_active_incidents",
        description=(
            "Return service incidents in a region. Use this BEFORE walking the "
            "customer through troubleshooting; if an active incident exists, "
            "defer to it. Use time_window='historical' to verify past outage "
            "claims."
        ),
        parameters={
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "Customer region, e.g. northeast-boston."},
                "time_window": {
                    "type": "string",
                    "enum": ["current", "historical", "all"],
                    "description": "Default 'current'.",
                    "default": "current",
                },
            },
            "required": ["region"],
        },
    ),
    ToolSpec(
        name="lookup_policy",
        description=(
            "Return policies applicable to an issue type, including authorized "
            "actions. Call this BEFORE any policy-gated write action."
        ),
        parameters={
            "type": "object",
            "properties": {
                "issue_type": {
                    "type": "string",
                    "enum": [
                        "outage_or_degradation",
                        "billing_dispute",
                        "account_change",
                        "technical_troubleshooting",
                        "other",
                    ],
                },
            },
            "required": ["issue_type"],
        },
    ),
    ToolSpec(
        name="get_escalation_path",
        description="Return the specialist queue and callback SLA for an issue type.",
        parameters={
            "type": "object",
            "properties": {
                "issue_type": {"type": "string"},
                "severity": {"type": "string", "default": "normal"},
            },
            "required": ["issue_type"],
        },
    ),
    ToolSpec(
        name="apply_credit",
        description=(
            "POLICY-GATED. Apply a service credit. Requires a policy_id whose "
            "authorized_actions include apply_credit at the requested amount. "
            "Look up the policy first with lookup_policy."
        ),
        parameters={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "amount": {"type": "number", "description": "Dollar amount."},
                "policy_id": {"type": "string", "description": "Policy ID that authorizes the credit."},
            },
            "required": ["customer_id", "amount", "policy_id"],
        },
    ),
    ToolSpec(
        name="schedule_callback",
        description=(
            "POLICY-GATED. Schedule a callback from a specialist queue. Requires "
            "a policy_id authorizing the callback."
        ),
        parameters={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "window": {"type": "string", "description": "When the callback happens, e.g. 'within 24 hours'."},
                "reason": {"type": "string", "description": "Short reason."},
                "policy_id": {"type": "string"},
            },
            "required": ["customer_id", "window", "reason", "policy_id"],
        },
    ),
    ToolSpec(
        name="send_message",
        description=(
            "POLICY-GATED. Send a templated customer message (case confirmation, "
            "ETA update, resolution notice). Requires a policy_id authorizing "
            "the message."
        ),
        parameters={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "template_id": {"type": "string", "description": "Template name, e.g. 'outage_acknowledgment'."},
                "params": {"type": "object", "description": "Template parameters."},
                "policy_id": {"type": "string"},
            },
            "required": ["customer_id", "template_id", "policy_id"],
        },
    ),
]
