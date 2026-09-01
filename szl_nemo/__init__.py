# SPDX-License-Identifier: Apache-2.0
"""szl-nemo — SOFTWARE/SURROGATE, not a kernel Hub CUDA kernel and not an LLM.

Approved path: deterministic doctrine rule_check() (R1–R5) plus the typed
Decision engine over it. model.joblib is quarantined and is not an
approved load path.
"""
from .engine import evaluate, evaluate_batch, input_hash
from .receipt import build_receipt, chain, verify_chain, verify_receipt
from .rules import RULE_IDS, rule_check
from .schema import ALLOW, BLOCK, REVIEW, Decision

__version__ = "0.3.0"
__all__ = [
    "ALLOW",
    "BLOCK",
    "REVIEW",
    "Decision",
    "RULE_IDS",
    "build_receipt",
    "chain",
    "evaluate",
    "evaluate_batch",
    "input_hash",
    "rule_check",
    "verify_chain",
    "verify_receipt",
    "__version__",
]
