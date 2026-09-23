# SPDX-License-Identifier: Apache-2.0
"""Hash-chained, honestly-unsigned receipts for szl-nemo decisions.

A receipt binds a Decision payload to its SHA-256 digest and to the
previous receipt in a chain (prev_receipt_sha256), giving anyone
integrity and ordering checks without this repo holding a signing key.
Receipts are UNSIGNED_HONEST. When SZL signs receipts, that happens in
the DSSE lane (szl-guardrail-receipt / szl-receipt), not here.

Deterministic: no clocks, no RNG. The same decision sequence always
produce the same receipt bytes.

Chain semantics reconciled from PR #2 (stephenlutar2-hash), adapted to
the merged szl.nemo.decision.v1 contract.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from .schema import RECEIPT_STATUS_UNSIGNED, Decision

RECEIPT_SCHEMA = "szl.nemo.receipt.v1"
GENESIS = "sha256:" + "0" * 64
_HEX = frozenset("0123456789abcdef")


def _sha256_canonical(payload: Dict[str, Any]) -> str:
    blob = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def _is_receipt_digest(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value[7:]
    return len(digest) == 64 and set(digest) <= _HEX


def build_receipt(
    decision: Decision,
    prev_receipt: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a verifiable, honestly-unsigned receipt for one Decision.

    Pass the previous receipt to extend a chain. A predecessor must itself
    verify before its sequence and digest are admitted into the new receipt;
    malformed or tampered history is never converted into a valid successor.
    """
    if prev_receipt is not None:
        if not verify_receipt(prev_receipt):
            raise ValueError("previous receipt failed verification")
        prev_digest = prev_receipt["receipt_sha256"]
        prev_sequence = prev_receipt["sequence"]
        sequence = prev_sequence + 1
        prev_link = prev_digest
    else:
        sequence = 0
        prev_link = GENESIS

    payload: Dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "sequence": sequence,
        "prev_receipt_sha256": prev_link,
        "decision": decision.to_dict(),
    }
    receipt = dict(payload)
    receipt["receipt_sha256"] = _sha256_canonical(payload)
    receipt["receipt_status"] = RECEIPT_STATUS_UNSIGNED
    return receipt


def verify_receipt(receipt: Any) -> bool:
    """Recompute the digest and check chain shape. Never raises."""
    try:
        if not isinstance(receipt, dict):
            return False
        if receipt.get("schema") != RECEIPT_SCHEMA:
            return False
        if receipt.get("receipt_status") != RECEIPT_STATUS_UNSIGNED:
            return False
        claimed = receipt.get("receipt_sha256")
        if not _is_receipt_digest(claimed):
            return False
        sequence = receipt.get("sequence")
        prev_link = receipt.get("prev_receipt_sha256")
        if type(sequence) is not int or sequence < 0:
            return False
        if not _is_receipt_digest(prev_link):
            return False
        if (sequence == 0) != (prev_link == GENESIS):
            return False
        decision = Decision.from_dict(receipt["decision"])
        payload = {
            "schema": RECEIPT_SCHEMA,
            "sequence": sequence,
            "prev_receipt_sha256": prev_link,
            "decision": decision.to_dict(),
        }
        return _sha256_canonical(payload) == claimed
    except Exception:
        return False


def verify_chain(receipts: Any) -> bool:
    """Verify every receipt and the linkage between them, in order."""
    if not isinstance(receipts, list) or not receipts:
        return False
    for i, receipt in enumerate(receipts):
        if not verify_receipt(receipt):
            return False
        if receipt["sequence"] != i:
            return False
        if i == 0:
            if receipt["prev_receipt_sha256"] != GENESIS:
                return False
        elif receipt["prev_receipt_sha256"] != receipts[i - 1]["receipt_sha256"]:
            return False
    return True


def chain(decisions: List[Decision]) -> List[Dict[str, Any]]:
    """Build an ordered receipt chain over a decision sequence."""
    receipts: List[Dict[str, Any]] = []
    for decision in decisions:
        receipts.append(build_receipt(decision, receipts[-1] if receipts else None))
    return receipts


__all__ = [
    "GENESIS",
    "RECEIPT_SCHEMA",
    "build_receipt",
    "chain",
    "verify_chain",
    "verify_receipt",
]
