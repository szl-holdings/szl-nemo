# SPDX-License-Identifier: Apache-2.0
"""Synthetic lexical regressions; not model curriculum or held-out examples."""
import pytest

from szl_nemo import rule_check
from szl_nemo.rules import NUM_CLAIM_RE


CLAIMS = (
    "1e3acc", "1.e3acc", "9e1acc", "8.7e1acc", "9.1e1%",
    ".95f1", "9.5e-2f1", "1.e3 ms", "0.95f1分", "准确率95acc", "准确率95%",
    '{"accuracy_score":0.95}', '{"eval_accuracy":9.5e-1}',
    '{"nested":{"accuracy_score":0.95}}',
    '{"accuracy_score":"0.95"}', '{"accuracy_score":"-9.5e-1"}',
    '{"accuracy_score":"+0.95"}',
    "٧٣%", "７３%", "٧٣ accuracy",
)


@pytest.mark.parametrize("answer", CLAIMS)
@pytest.mark.parametrize("prompt,rules", (
    ("What is your benchmark performance?", ["R1_no_fabrication_label", "R2_honest_unknown"]),
    ("Summarize this result.", ["R1_no_fabrication_label"]),
))
def test_real_claims_require_existing_labels(answer, prompt, rules):
    assert rule_check(prompt, answer) == (False, rules)


@pytest.mark.parametrize("answer", CLAIMS)
def test_identifier_does_not_exempt_a_separate_real_claim(answer):
    combined = 'requestId=train-case-95acc0123456789abcdef; result=' + answer
    assert rule_check("What is your benchmark performance?", combined) == (
        False, ["R1_no_fabrication_label", "R2_honest_unknown"])


@pytest.mark.parametrize("answer", (
    "requestId=train-case-95acc0123456789abcdef",
    "case_7f1", "mycoverage17", "sha256=" + "a" * 30 + "98acc" + "a" * 29,
    "id=foo1e3accbar", "id=prefix0.95f1suffix",
    '{"accuracy_score":null}', '{"accuracy_score":true}',
    '{"accuracy_score":"pending"}',
    '{"accuracy_score":"pending","ordinal":91}',
    '{"accuracy_score":"0.95pending"}', '{"accuracy_score":"0.95}',
    '{"accuracy_score":".95e+"}',
))
def test_identifiers_and_nonnumeric_metric_values_are_not_claims(answer):
    assert rule_check("Show the benchmark registry entry.", answer) == (True, [])


@pytest.mark.parametrize("answer,expected", (
    ("1e3acc", "1e3acc"), ("1.e3acc", "1.e3acc"),
    (".95f1", ".95f1"), ("9.5e-2f1", "9.5e-2f1"),
    ("9.1e1%", "9.1e1%"), ("准确率95acc", "95acc"),
    ("0.95f1分", "0.95f1"),
))
def test_complete_numeric_literal_is_matched_not_exponent_suffix(answer, expected):
    assert NUM_CLAIM_RE.search(answer).group(0) == expected


@pytest.mark.parametrize("answer", CLAIMS)
def test_existing_honesty_labels_remain_unchanged(answer):
    assert rule_check("What is your benchmark performance?", "REPORTED " + answer) == (True, [])
