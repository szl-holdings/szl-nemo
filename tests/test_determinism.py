# SPDX-License-Identifier: Apache-2.0
"""Determinism: same input, same bytes, same digests — no clocks, no RNG."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from szl_nemo import build_receipt, evaluate
from szl_nemo.schema import canonical_json, sha256_hex

PROMPT = "What's your MMLU?"
ANSWER = "I aim for honesty; my MMLU is 73."


def test_decision_digest_is_deterministic():
    first = evaluate(PROMPT, ANSWER)
    second = evaluate(PROMPT, ANSWER)
    assert first.input_sha256 == second.input_sha256
    assert first.to_json(indent=None) == second.to_json(indent=None)


def test_receipt_digest_is_deterministic():
    decision = evaluate(PROMPT, ANSWER)
    first = build_receipt(decision)
    second = build_receipt(decision)
    assert first["receipt_sha256"] == second["receipt_sha256"]
    assert first == second


def test_canonical_json_is_key_order_invariant():
    left = {"b": 1, "a": {"d": 2, "c": 3}}
    right = {"a": {"c": 3, "d": 2}, "b": 1}
    assert canonical_json(left) == canonical_json(right)
    assert sha256_hex(left) == sha256_hex(right)


def test_receipt_contains_no_timestamps_or_randomness():
    decision = evaluate(PROMPT, ANSWER)
    receipt = build_receipt(decision)
    for forbidden in ("timestamp", "time", "date", "nonce", "random"):
        assert forbidden not in receipt, forbidden
