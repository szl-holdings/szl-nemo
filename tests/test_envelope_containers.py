"""Malformed containers must not be erased into an empty, valid envelope."""
import pytest

from szl_nemo import ALLOW, BLOCK
from szl_nemo.envelope import canonical_sha256, evaluate_envelope
from test_envelope import _envelope


def empty_envelope():
    value = _envelope("PRE_GENERATION")
    value["evidence"].update(grounding_required=False, handles=[], items=[],
                             evidence_set_sha256=canonical_sha256([]))
    value["formulas"].update(requested_formula_ids=[], applications=[],
                             authorization_basis_ids=[])
    return value


@pytest.mark.parametrize("section,field,rule", [
    ("evidence", "handles", "E3_scoped_evidence_binding"),
    ("evidence", "items", "E3_scoped_evidence_binding"),
    ("formulas", "requested_formula_ids", "E4_formula_authority"),
    ("formulas", "applications", "E4_formula_authority"),
    ("formulas", "authorization_basis_ids", "E4_formula_authority"),
    (None, "witness_history", "E8_witness_stage_order"),
])
@pytest.mark.parametrize("bad", [None, False, 0, "", "not-an-array", {}])
def test_malformed_arrays_block_instead_of_becoming_empty(section, field, rule, bad):
    value = empty_envelope()
    target = value[section] if section else value
    target[field] = bad
    decision = evaluate_envelope(value)
    assert decision.decision == BLOCK
    assert rule in decision.violated_rules


@pytest.mark.parametrize("field,rule", [
    ("tool_intent", "E7_tool_admission"),
    ("action_admission", "E7_tool_admission"),
    ("receipt", "E7_tool_admission"),
    ("tool_result", "E9_postcondition_binding"),
    ("postcondition", "E9_postcondition_binding"),
])
@pytest.mark.parametrize("bad", [False, 0, "", "not-an-object", []])
def test_malformed_optional_objects_block_instead_of_disappearing(field, rule, bad):
    value = empty_envelope()
    value[field] = bad
    decision = evaluate_envelope(value)
    assert decision.decision == BLOCK
    assert rule in decision.violated_rules


@pytest.mark.parametrize("absent", [None, {}])
def test_explicit_empty_arrays_and_absent_optional_objects_remain_valid(absent):
    value = empty_envelope()
    for field in ("tool_intent", "action_admission", "receipt", "tool_result", "postcondition"):
        value[field] = absent
    assert evaluate_envelope(value).decision == ALLOW
