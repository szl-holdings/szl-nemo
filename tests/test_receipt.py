# SPDX-License-Identifier: Apache-2.0
"""Receipt contract: hashing, chaining, tamper detection, never-raises
verification. Receipts are UNSIGNED_HONEST by construction."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from szl_nemo import evaluate  # noqa: E402
from szl_nemo.receipt import (  # noqa: E402
    GENESIS,
    RECEIPT_SCHEMA,
    build_receipt,
    chain,
    verify_chain,
    verify_receipt,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALLOW_PAIR = ("What's your MMLU?", "UNKNOWN - no benchmarks have been run.")
BLOCK_PAIR = ("What's your MMLU?", "My MMLU is 73.")
REVIEW_PAIR = ("", "")


def test_genesis_receipt_shape():
    receipt = build_receipt(evaluate(*ALLOW_PAIR))
    assert receipt["schema"] == RECEIPT_SCHEMA
    assert receipt["sequence"] == 0
    assert receipt["prev_receipt_sha256"] == GENESIS
    assert receipt["receipt_status"] == "UNSIGNED_HONEST"
    assert receipt["receipt_sha256"].startswith("sha256:")
    assert verify_receipt(receipt) is True


def test_chain_links_and_sequences():
    receipts = chain([evaluate(*ALLOW_PAIR), evaluate(*BLOCK_PAIR), evaluate(*ALLOW_PAIR)])
    assert [r["sequence"] for r in receipts] == [0, 1, 2]
    assert receipts[1]["prev_receipt_sha256"] == receipts[0]["receipt_sha256"]
    assert receipts[2]["prev_receipt_sha256"] == receipts[1]["receipt_sha256"]
    assert verify_chain(receipts) is True


def test_tampered_decision_breaks_receipt():
    receipt = build_receipt(evaluate(*BLOCK_PAIR))
    tampered = copy.deepcopy(receipt)
    tampered["decision"]["decision"] = "ALLOW"
    assert verify_receipt(tampered) is False


def test_tampered_sequence_breaks_receipt():
    receipt = build_receipt(evaluate(*ALLOW_PAIR))
    tampered = dict(receipt, sequence=7)
    assert verify_receipt(tampered) is False


def test_broken_link_breaks_chain():
    receipts = chain([evaluate(*ALLOW_PAIR), evaluate(*BLOCK_PAIR)])
    broken = [receipts[0], dict(receipts[1], prev_receipt_sha256=GENESIS)]
    assert verify_chain(broken) is False


def test_reordered_chain_fails():
    receipts = chain([evaluate(*ALLOW_PAIR), evaluate(*BLOCK_PAIR), evaluate(*ALLOW_PAIR)])
    assert verify_chain([receipts[0], receipts[2], receipts[1]]) is False


def test_verify_never_raises_on_garbage():
    for garbage in (None, 42, "receipt", [], {}, {"schema": RECEIPT_SCHEMA},
                    {"schema": RECEIPT_SCHEMA, "receipt_sha256": 1, "sequence": "0"},
                    {"schema": RECEIPT_SCHEMA, "sequence": 0,
                     "prev_receipt_sha256": GENESIS, "decision": {"bogus": 1}}):
        assert verify_receipt(garbage) is False
    assert verify_chain([]) is False
    assert verify_chain("not a list") is False


def test_build_receipt_rejects_malformed_prev():
    try:
        build_receipt(evaluate(*ALLOW_PAIR), prev_receipt={"sequence": "x"})
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_receipts_are_deterministic():
    a = chain([evaluate(*ALLOW_PAIR), evaluate(*BLOCK_PAIR)])
    b = chain([evaluate(*ALLOW_PAIR), evaluate(*BLOCK_PAIR)])
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_review_decision_receipts_too():
    receipt = build_receipt(evaluate(*REVIEW_PAIR))
    assert receipt["decision"]["decision"] == "REVIEW"
    assert verify_receipt(receipt) is True


def test_cli_receipt_verify_roundtrip():
    receipts = chain([evaluate(*ALLOW_PAIR), evaluate(*BLOCK_PAIR)])
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "chain.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(receipts, fh)
        proc = subprocess.run(
            [sys.executable, "-m", "szl_nemo", "receipt-verify", path],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert "RECEIPT OK" in proc.stdout

        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            json.dump({"schema": RECEIPT_SCHEMA, "sequence": 0}, fh)
        proc = subprocess.run(
            [sys.executable, "-m", "szl_nemo", "receipt-verify", bad],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert proc.returncode == 1
