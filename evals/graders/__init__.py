"""Graders. See `code_based.py` for deterministic checks, `model_based.py`
for the LLM-as-judge check.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GraderResult:
    """One grader's verdict on a single trace."""

    grader_name: str
    passed: bool
    score: float  # 0.0 to 1.0
    explanation: str
    expected: Any = None
    actual: Any = None
    skipped: bool = False  # for conditional graders (e.g., credit_amount only applies to some scenarios)
