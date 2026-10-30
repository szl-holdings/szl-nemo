# SPDX-License-Identifier: Apache-2.0
"""szl-nemo — deterministic doctrine and inference-envelope witness.

Approved paths:
- prompt/answer R1-R5 rule_check + typed Decision engine;
- structured E1-E10 inference-envelope witness;
- unsigned triad binder for a proposal, NVML joules or null, and Lambda.

This is SOFTWARE, not a Kernel Hub CUDA kernel, not an LLM, and not Nemotron.
``model.joblib`` remains quarantined and is not an approved load path.
"""
from .engine import evaluate, evaluate_batch, input_hash
from .envelope import (
    ENVELOPE_RULE_IDS,
    ENVELOPE_RULE_VERSION,
    ENVELOPE_SCHEMA_VERSION,
    LOCKED_PROVEN_FORMULA_IDS,
    STAGES,
    TRUTH_LABELS,
    envelope_check,
    envelope_input_hash,
    evaluate_envelope,
)
from .receipt import build_receipt, chain, verify_chain, verify_receipt
from .rules import RULE_IDS, rule_check
from .schema import ALLOW, BLOCK, REVIEW, Decision
from .triad import (
    LAMBDA_STATUS_LABEL,
    TRIAD_SCHEMA,
    evaluate_triad,
)

__version__ = "0.4.2"
__all__ = [
    "ALLOW",
    "BLOCK",
    "REVIEW",
    "Decision",
    "ENVELOPE_RULE_IDS",
    "ENVELOPE_RULE_VERSION",
    "ENVELOPE_SCHEMA_VERSION",
    "LOCKED_PROVEN_FORMULA_IDS",
    "LAMBDA_STATUS_LABEL",
    "RULE_IDS",
    "STAGES",
    "TRIAD_SCHEMA",
    "TRUTH_LABELS",
    "build_receipt",
    "chain",
    "envelope_check",
    "envelope_input_hash",
    "evaluate",
    "evaluate_batch",
    "evaluate_envelope",
    "evaluate_triad",
    "input_hash",
    "rule_check",
    "verify_chain",
    "verify_receipt",
    "__version__",
]
