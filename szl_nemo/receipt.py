# SPDX-License-Identifier: Apache-2.0
"""Hash-chained, honestly-unsigned receipts for szl-nemo decisions.

A receipt binds a decision payload to its SHA-256 digest and optionally to
the previous receipt in a chain (prev_receipt_sha256). Receipts are
UNSIGNED_HONEST: integrity and ordering are checkable by anyone, but no
signature identity is claimed. When SZL signs receipts, that happens in the
DSSE lane (szl-receipt), not here.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .schema import RECEIPT_SCHEMA, UNSIGNED_HONEST, Decision, sha256_hex

GENESIS = "sha256:" + "0" * 64


def build_receipt(
    decision: Decision,
    prev_receipt: Optional[Dict[str, Any]] = None,
    sequence: int = 0,
) -> Dict[str, Any]:
    """Build a verifiable, honestly-unsigned receipt for a decision."""
    if prev_receipt is not None:
        prev_digest = prev_receipt.get("receipt_sha256")
        if not isinstance(prev_digest, str):
            raise ValueError("previous receipt carries no receipt_sha256")
        prev_sequence = prev_receipt.get("sequence")
        if not isinstance(prev_sequence, int) or prev_sequence < 0:
            raise ValueError("previous receipt carries an invalid sequence")
        sequence = prev_sequence + 1
        prev_link = prev_digest
    else:
        prev_link = GENESIS

    payload: Dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "sequence": sequence,
        "prev_receipt_sha256": prev_link,
        "decision": decision.payload(),
    }
    receipt = dict(payload)
    receipt["receipt_sha256"] = sha256_hex(payload)
    receipt["receipt_status"] = UNSIGNED_HONEST
    return receipt


def verify_receipt(receipt: Dict[str, Any]) -> bool:
    """Recompute the digest and check chain shape. Never raises."""
    try:
        if not isinstance(receipt, dict):
            return False
        if receipt.get("schema") != RECEIPT_SCHEMA:
            return False
        claimed = receipt.get("receipt_sha256")
        if not isinstance(claimed, str):
            return False
        sequence = receipt.get("sequence")
        prev_link = receipt.get("prev_receipt_sha256")
        if not isinstance(sequence, int) or sequence < 0:
            return False
        if not isinstance(prev_link, str) or not prev_link.startswith("sha256:"):
            return False
        if (sequence == 0) != (prev_link == GENESIS):
            return False
        # Decision.parse re-validates the embedded decision contract.
        decision = Decision.parse(receipt.get("decision"))
        payload = {
            "schema": RECEIPT_SCHEMA,
            "sequence": sequence,
            "prev_receipt_sha256": prev_link,
            "decision": decision.payload(),
        }
        return sha256_hex(payload) == claimed
    except (ValueError, TypeError, KeyError):
        return False


__all__ = ["GENESIS", "build_receipt", "verify_receipt"]
