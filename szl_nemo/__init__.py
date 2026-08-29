# SPDX-License-Identifier: Apache-2.0
"""szl-nemo — SOFTWARE/SURROGATE, not a kernel Hub CUDA kernel and not an LLM.

Approved path: deterministic doctrine rule_check() (R1–R5).
model.joblib is quarantined and is not an approved load path.
"""
from .rules import rule_check, RULE_IDS

__version__ = "0.1.0"
__all__ = ["rule_check", "RULE_IDS", "__version__"]
