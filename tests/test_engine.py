# SPDX-License-Identifier: Apache-2.0
"""Contract tests for the typed Decision engine over rule_check."""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from szl_nemo import __version__, rule_check  # noqa: E402
from szl_nemo.engine import canonical_input, evaluate, evaluate_batch, input_hash  # noqa: E402
from szl_nemo.schema import (  # noqa: E402
    ALLOW,
    BLOCK,
    RECEIPT_STATUS_UNSIGNED,
    RULE_VERSION,
    SCHEMA_VERSION,
    decision_from_json,
)

CONFORM = (
    "How good is the model?",
    "UNKNOWN - no benchmarks have been run on SZL hardware.",
)
VIOLATION = ("What's your MMLU?", "My MMLU is 73.")


def test_allow_decision_matches_rule_check():
    ok, _ = rule_check(*CONFORM)
    decision = evaluate(*CONFORM)
    assert ok is True
    assert decision.decision == ALLOW
    assert decision.violated_rules == ()
    assert decision.reasons == ()


def test_block_decision_carries_rules_and_reasons():
    decision = evaluate(*VIOLATION)
    assert decision.decision == BLOCK
    assert "R1_no_fabrication_label" in decision.violated_rules
    assert len(decision.reasons) == len(decision.violated_rules)
    assert all(isinstance(reason, str) and reason for reason in decision.reasons)


def test_every_violated_rule_has_a_human_reason():
    decision = evaluate("Explain Λ and trust.", "Λ is proven. Trust is 1.0 trust.")
    assert decision.decision == BLOCK
    assert len(decision.reasons) == len(decision.violated_rules)


def test_input_hash_is_sha256_of_canonical_pair():
    digest = input_hash(*CONFORM)
    assert digest.startswith("sha256:")
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
    # canonical form is sorted, compact, utf-8 safe
    assert canonical_input("b", "a") == '{"answer":"a","prompt":"b"}'


def test_decision_serializes_to_canonical_stable_json():
    decision = evaluate(*VIOLATION)
    text = decision.to_json()
    assert text == json.dumps(
        json.loads(text), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    roundtrip = decision_from_json(text)
    assert roundtrip == decision


def test_contract_fields_present():
    data = evaluate(*CONFORM).to_dict()
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["rule_version"] == RULE_VERSION
    assert data["receipt_status"] == RECEIPT_STATUS_UNSIGNED
    assert data["decision"] in (ALLOW, BLOCK)


def test_receipt_status_is_honestly_unsigned():
    # No signing key exists in this repo; the contract must say so.
    assert evaluate(*CONFORM).receipt_status == RECEIPT_STATUS_UNSIGNED


def test_batch_evaluates_in_order():
    decisions = evaluate_batch(
        [
            {"prompt": CONFORM[0], "answer": CONFORM[1]},
            {"prompt": VIOLATION[0], "answer": VIOLATION[1]},
        ]
    )
    assert [d.decision for d in decisions] == [ALLOW, BLOCK]


def test_batch_rejects_malformed_record():
    try:
        evaluate_batch([{"prompt": "missing answer"}])
    except ValueError as exc:
        assert "record 0" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_version_is_semverish():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)
