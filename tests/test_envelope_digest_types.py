"""Digest and revision fields must bind JSON strings, never coerced numbers."""
import pytest

from szl_nemo import ALLOW, BLOCK
from szl_nemo.envelope import canonical_sha256, evaluate_envelope
from test_envelope import _envelope


DIGEST_FIELDS = [
    (("scope", "principal_id_sha256"), "E3_scoped_evidence_binding"),
    (("scope", "tenant_id_sha256"), "E3_scoped_evidence_binding"),
    (("evidence", "items", 0, "sha256"), "E3_scoped_evidence_binding"),
    (("evidence", "evidence_set_sha256"), "E3_scoped_evidence_binding"),
    (("formulas", "applications", 0, "basis_sha256"), "E4_formula_authority"),
    (("tool_intent", "sha256"), "E7_tool_admission"),
    (("receipt", "sha256"), "E7_tool_admission"),
    (("tool_result", "sha256"), "E9_postcondition_binding"),
    (("postcondition", "details_sha256"), "E9_postcondition_binding"),
    (("claims", 0, "statement_sha256"), "E10_truth_label_binding"),
]
REVISION_FIELDS = [
    (("model", "revision"), "E2_pinned_model_runtime_identity"),
    (("model", "adapter_revision"), "E2_pinned_model_runtime_identity"),
    (("model", "tokenizer_revision"), "E2_pinned_model_runtime_identity"),
    (("model", "template_revision"), "E2_pinned_model_runtime_identity"),
    (("scope", "policy_revision"), "E3_scoped_evidence_binding"),
    (("formulas", "formal_source_commit"), "E4_formula_authority"),
    (("formulas", "kernel_source_commit"), "E4_formula_authority"),
]


def replace(value, path, replacement):
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    if path[:2] == ("evidence", "items"):
        # Keep the collection binding valid so the item's type is the only fault.
        value["evidence"]["evidence_set_sha256"] = canonical_sha256(
            value["evidence"]["items"]
        )


@pytest.mark.parametrize("path,rule", DIGEST_FIELDS + REVISION_FIELDS)
@pytest.mark.parametrize("bad", [None, False, True, 1.0, [], {}, ""])
def test_malformed_digest_and_revision_types_block(path, rule, bad):
    value = _envelope("POST_TOOL")
    replace(value, path, bad)
    decision = evaluate_envelope(value)
    assert decision.decision == BLOCK
    assert rule in decision.violated_rules


@pytest.mark.parametrize("path,rule", DIGEST_FIELDS)
def test_hex_shaped_integer_digest_is_not_a_digest(path, rule):
    value = _envelope("POST_TOOL")
    replace(value, path, int("1" * 64))
    decision = evaluate_envelope(value)
    assert decision.decision == BLOCK
    assert rule in decision.violated_rules


@pytest.mark.parametrize("path,rule", REVISION_FIELDS)
def test_hex_shaped_integer_revision_is_not_a_revision(path, rule):
    value = _envelope("POST_TOOL")
    replace(value, path, int("1" * 40))
    decision = evaluate_envelope(value)
    assert decision.decision == BLOCK
    assert rule in decision.violated_rules


@pytest.mark.parametrize("path,_rule", DIGEST_FIELDS)
def test_string_digest_case_normalization_is_preserved(path, _rule):
    value = _envelope("POST_TOOL")
    target = value
    for key in path:
        target = target[key]
    replace(value, path, target.upper())
    assert evaluate_envelope(value).decision == ALLOW


@pytest.mark.parametrize("path,_rule", REVISION_FIELDS)
@pytest.mark.parametrize("revision", ["A" * 40, "sha256:" + "A" * 64])
def test_string_revision_case_normalization_is_preserved(path, _rule, revision):
    value = _envelope("POST_TOOL")
    replace(value, path, revision)
    assert evaluate_envelope(value).decision == ALLOW


def test_explicit_no_adapter_string_remains_valid():
    value = _envelope("POST_TOOL")
    value["model"]["adapter_revision"] = "NONE"
    assert evaluate_envelope(value).decision == ALLOW
