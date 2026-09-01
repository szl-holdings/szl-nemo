# SPDX-License-Identifier: Apache-2.0
"""Typed decision contract for the szl-nemo doctrine kernel.

Stdlib only. This is SOFTWARE: a deterministic contract over
szl_nemo.rules.rule_check (R1-R5, ground truth). It is not a trained
model, not Nemotron, and not a CUDA kernel.

Honesty boundary: decisions are deterministic outputs of rule_check.
receipt_status is always UNSIGNED_HONEST because this repository holds
no signing key; a receipt that has not been signed must say so.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Tuple

SCHEMA_VERSION = "szl.nemo.decision.v1"
RULE_VERSION = "doctrine-v11/R1-R5"
RECEIPT_STATUS_UNSIGNED = "UNSIGNED_HONEST"

ALLOW = "ALLOW"
BLOCK = "BLOCK"
# REVIEW is exactly one case: an empty/blank prompt or answer carries no
# doctrine signal, so the kernel refuses to silently ALLOW it. Anything
# with real content gets the binary rule_check verdict. (Tier semantics
# reconciled from PR #2.)
REVIEW = "REVIEW"
DECISIONS = (ALLOW, BLOCK, REVIEW)


@dataclass(frozen=True)
class Decision:
    """One deterministic doctrine decision over a (prompt, answer) pair."""

    decision: str
    violated_rules: Tuple[str, ...]
    rule_version: str
    input_hash: str
    schema_version: str = SCHEMA_VERSION
    receipt_status: str = RECEIPT_STATUS_UNSIGNED
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision,
            "violated_rules": list(self.violated_rules),
            "reasons": list(self.reasons),
            "rule_version": self.rule_version,
            "input_hash": self.input_hash,
            "receipt_status": self.receipt_status,
        }

    def to_json(self) -> str:
        """Canonical JSON: stable byte output for hashing and receipts."""
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Decision":
        return cls(
            decision=data["decision"],
            violated_rules=tuple(data.get("violated_rules", ())),
            rule_version=data["rule_version"],
            input_hash=data["input_hash"],
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            receipt_status=data.get("receipt_status", RECEIPT_STATUS_UNSIGNED),
            reasons=tuple(data.get("reasons", ())),
        )


def decision_from_json(text: str) -> Decision:
    return Decision.from_dict(json.loads(text))


__all__: List[str] = [
    "ALLOW",
    "BLOCK",
    "DECISIONS",
    "Decision",
    "RECEIPT_STATUS_UNSIGNED",
    "RULE_VERSION",
    "SCHEMA_VERSION",
    "decision_from_json",
]
