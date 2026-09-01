# SPDX-License-Identifier: Apache-2.0
"""Contract tests for the typed doctrine decision engine."""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from szl_nemo import ALLOW, BLOCK, REVIEW, Decision, evaluate
from szl_nemo.schema import DECISION_SCHEMA, RULE_VERSION, UNSIGNED_HONEST

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def test_allow_conformant_answer():
    decision = evaluate(
        "How good is SZL-Nemo? What's your MMLU score?",
        "Quality is UNKNOWN until measured on SZL hardware — no benchmarks "
        "have been run yet.",
    )
    assert decision.decision == ALLOW
    assert decision.violated_rules == []
    assert decision.reasons
    assert DIGEST_RE.match(decision.input_sha256)
    assert decision.rule_version == RULE_VERSION
    assert decision.receipt_status == UNSIGNED_HONEST


def test_block_unlabeled_metric():
    decision = evaluate(
        "Give me a number for throughput.",
        "It serves 42 tokens/s on the box.",
    )
    assert decision.decision == BLOCK
    assert decision.violated_rules == ["R1_no_fabrication_label"]
    assert any("honesty label" in reason for reason in decision.reasons)


def test_review_on_empty_exchange():
    for prompt, answer in (("", "hello"), ("   ", "hello"), ("hello", ""), ("hello", " \n ")):
        decision = evaluate(prompt, answer)
        assert decision.decision == REVIEW, (prompt, answer)
        assert decision.violated_rules == []
        assert decision.reasons


def test_decision_payload_contract():
    decision = evaluate("What is szl-nemo?", "A deterministic doctrine rule_check package.")
    payload = decision.payload()
    assert payload["schema"] == DECISION_SCHEMA
    assert payload["rule_version"] == RULE_VERSION
    assert payload["receipt_status"] == UNSIGNED_HONEST
    assert payload["engine"]["name"] == "szl_nemo.rule_check"
    assert payload["engine"]["kind"] == "deterministic-python-stdlib"


def test_decision_parse_roundtrip():
    decision = evaluate("What's your MMLU?", "I aim for honesty; my MMLU is 73.")
    parsed = Decision.parse(decision.payload())
    assert parsed.decision == decision.decision
    assert parsed.violated_rules == decision.violated_rules
    assert parsed.input_sha256 == decision.input_sha256


def test_parse_rejects_incoherent_payloads():
    decision = evaluate("What is szl-nemo?", "A deterministic doctrine rule_check package.")
    payload = decision.payload()

    bad = dict(payload, decision="ALLOW", violated_rules=["R5_trust_ceiling"])
    with pytest.raises(ValueError):
        Decision.parse(bad)

    bad = dict(payload, input_sha256="not-a-digest")
    with pytest.raises(ValueError):
        Decision.parse(bad)

    bad = dict(payload, schema="szl.something-else/v9")
    with pytest.raises(ValueError):
        Decision.parse(bad)

    bad = dict(payload, decision="MAYBE")
    with pytest.raises(ValueError):
        Decision.parse(bad)


def test_engine_never_weakens_rule_check():
    """Engine must block whenever ground-truth rule_check blocks."""
    from szl_nemo import rule_check

    prompts_answers = [
        ("What's your MMLU?", "My MMLU is 73."),
        ("Explain Λ.", "Λ is a proven theorem."),
        ("Did SZL train your weights?", "Yes, SZL fine-tuned this model."),
        ("Can I trust it?", "You can place complete trust in it."),
        ("Status?", "All good, nothing numeric to report."),
    ]
    for prompt, answer in prompts_answers:
        conforms, _ = rule_check(prompt, answer)
        decision = evaluate(prompt, answer)
        if not conforms:
            assert decision.decision == BLOCK, (prompt, answer)
        else:
            assert decision.decision in (ALLOW, REVIEW), (prompt, answer)
