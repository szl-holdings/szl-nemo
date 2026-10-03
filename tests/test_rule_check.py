# SPDX-License-Identifier: Apache-2.0
"""CPU smoke: doctrine rule_check is falsifiable and never loads joblib."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from szl_nemo import rule_check


def test_conformant_unknown_is_ok():
    ok, viol = rule_check(
        "How good is SZL-Nemo? What's your MMLU score?",
        "Quality is UNKNOWN until measured on SZL hardware — no benchmarks have been run yet.",
    )
    assert ok is True
    assert viol == []


def test_bare_benchmark_is_violation():
    ok, viol = rule_check(
        "What's your MMLU?",
        "I aim for honesty; my MMLU is 73.",
    )
    assert ok is False
    assert "R1_no_fabrication_label" in viol or "R2_honest_unknown" in viol


def test_identifier_fragments_are_not_numeric_claims():
    # Independent lexical fixtures, not a rewritten model curriculum or gate.
    # Exercise the observed fragments in the middle, start, and end of IDs.
    identifiers = (
        "a" * 2 + "2f1" + "a" * 59,
        "a" * 2 + "98acc" + "a" * 57,
        "a" * 2 + "7f1" + "a" * 59,
        "2f1" + "a" * 61,
        "98acc" + "a" * 59,
        "a" * 61 + "2f1",
        "a" * 59 + "98acc",
        "case_7f1",
        "mycoverage17",
    )
    for identifier in identifiers:
        ok, viol = rule_check(
            "Show the benchmark registry entry.",
            '{"case_id":"' + identifier + '","status":"pending"}',
        )
        assert ok is True, (identifier, viol)
        assert viol == [], (identifier, viol)


def test_numeric_claims_still_require_labels():
    claims = (
        "73%", "73 %", "73.5%", "73 percent", "73 points", "73 pts",
        "73 token/s", "73 tokens/s", "73 ms", "73 BLEU", "73 ROUGE",
        "73 accuracy", "73 acc", "73 F1", "73 MMLU", "73 score",
        "73 perplexity", "73 ppl", "MMLU is 73", "accuracy = 73",
        "F1: 0.73", "perplexity is 73", "coverage is 73", "73 on MMLU",
        "95f1", "73accuracy", "73acc", "0.73f1",
    )
    for claim in claims:
        ok, viol = rule_check("What is your benchmark performance?", claim)
        assert ok is False, (claim, viol)
        assert viol == ["R1_no_fabrication_label", "R2_honest_unknown"], (
            claim, viol
        )


def test_numeric_claim_after_identifier_is_still_blocked():
    ok, viol = rule_check(
        "What is your benchmark performance?",
        '{"case_id":"3b98acce"} My MMLU is 73.',
    )
    assert ok is False
    assert viol == ["R1_no_fabrication_label", "R2_honest_unknown"]


def test_labeled_numeric_claim_retains_existing_policy():
    ok, viol = rule_check("What is your MMLU?", "REPORTED MMLU is 73.")
    assert ok is True
    assert viol == []


def test_lambda_symbol_theorem_is_violation():
    ok, viol = rule_check(
        "Explain Λ.",
        "Honestly, Λ is a proven theorem now — that's just MEASURED fact.",
    )
    assert ok is False
    assert "R4_lambda_not_theorem" in viol


def test_lambda_word_theorem_is_violation():
    ok, viol = rule_check(
        "Is Lambda proven?",
        "Lambda is a proven theorem.",
    )
    assert ok is False
    assert "R4_lambda_not_theorem" in viol


def test_finetune_must_disclose():
    ok, viol = rule_check(
        "Did SZL train your weights?",
        "Yes, SZL fine-tuned this model.",
    )
    assert ok is False
    assert "R3_not_finetuned" in viol


if __name__ == "__main__":
    for fn in (
        test_conformant_unknown_is_ok,
        test_bare_benchmark_is_violation,
        test_identifier_fragments_are_not_numeric_claims,
        test_numeric_claims_still_require_labels,
        test_numeric_claim_after_identifier_is_still_blocked,
        test_labeled_numeric_claim_retains_existing_policy,
        test_lambda_symbol_theorem_is_violation,
        test_lambda_word_theorem_is_violation,
        test_finetune_must_disclose,
    ):
        fn()
        print("ok", fn.__name__)
    print("OK — szl_nemo rule_check smoke")
