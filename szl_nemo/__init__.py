# SPDX-License-Identifier: Apache-2.0
"""szl-nemo — SOFTWARE/SURROGATE, not a kernel Hub CUDA kernel and not an LLM.

Approved path: deterministic doctrine rule_check() (R1–R5) with a typed
decision contract (evaluate → Decision), hash-chained UNSIGNED_HONEST
receipts, and a fail-closed CLI. model.joblib is quarantined and is not an
approved load path.
"""
from .engine import evaluate
from .receipt import build_receipt, verify_receipt
from .rules import RULE_IDS, rule_check
from .schema import ALLOW, BLOCK, REVIEW, Decision, RuleCheckInput

__version__ = "0.2.0"
__all__ = [
    "ALLOW",
    "BLOCK",
    "REVIEW",
    "Decision",
    "RuleCheckInput",
    "RULE_IDS",
    "build_receipt",
    "evaluate",
    "rule_check",
    "verify_receipt",
    "__version__",
]
