# SPDX-License-Identifier: Apache-2.0
"""Receipt chain: build, verify, link, and detect tampering."""
from __future__ import annotations

import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from szl_nemo import build_receipt, evaluate, verify_receipt
from szl_nemo.receipt import GENESIS
from szl_nemo.schema import RECEIPT_SCHEMA, UNSIGNED_HONEST


def _decision(prompt: str = "What is szl-nemo?", answer: str = "A deterministic doctrine rule_check package."):
    return evaluate(prompt, answer)


def test_genesis_receipt_verifies():
    receipt = build_receipt(_decision())
    assert receipt["schema"] == RECEIPT_SCHEMA
    assert receipt["sequence"] == 0
    assert receipt["prev_receipt_sha256"] == GENESIS
    assert receipt["receipt_status"] == UNSIGNED_HONEST
    assert verify_receipt(receipt) is True


def test_chain_links_and_verifies():
    first = build_receipt(_decision())
    second = build_receipt(
        _decision("Give me a number for throughput.", "It serves 42 tokens/s on the box."),
        prev_receipt=first,
    )
    assert second["sequence"] == 1
    assert second["prev_receipt_sha256"] == first["receipt_sha256"]
    assert verify_receipt(second) is True


def test_tampered_decision_fails_verification():
    receipt = build_receipt(_decision())
    tampered = copy.deepcopy(receipt)
    tampered["decision"]["decision"] = "BLOCK"
    assert verify_receipt(tampered) is False


def test_tampered_chain_link_fails_verification():
    first = build_receipt(_decision())
    second = build_receipt(_decision(), prev_receipt=first)
    tampered = copy.deepcopy(second)
    tampered["prev_receipt_sha256"] = GENESIS
    assert verify_receipt(tampered) is False


def test_garbage_fails_closed():
    assert verify_receipt({}) is False
    assert verify_receipt({"schema": RECEIPT_SCHEMA}) is False
    assert verify_receipt("not a dict") is False  # type: ignore[arg-type]
    assert verify_receipt(None) is False  # type: ignore[arg-type]


def test_build_receipt_requires_valid_previous():
    import pytest

    with pytest.raises(ValueError):
        build_receipt(_decision(), prev_receipt={"no_digest": True})
