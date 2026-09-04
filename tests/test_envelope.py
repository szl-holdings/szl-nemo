# SPDX-License-Identifier: Apache-2.0
"""Structured inference-envelope witness: authority, evidence, and replay tests."""
from __future__ import annotations

import copy

from szl_nemo import ALLOW, BLOCK, REVIEW
from szl_nemo.envelope import canonical_sha256, evaluate_envelope

REV_A = "a" * 40
REV_B = "b" * 40
REV_C = "c" * 40
DIGEST = "d" * 64
POLICY_REV = "sha256:" + ("e" * 64)
LOCKED_EIGHT = ["F1", "F4", "F7", "F11", "F12", "F18", "F19", "F22"]
EVIDENCE = [
    {
        "node_id": "formula:locked-eight",
        "source": "szl-holdings/lutar-lean",
        "sha256": DIGEST,
    }
]


def _envelope(stage: str = "POST_GENERATION") -> dict:
    histories = {
        "PRE_GENERATION": [],
        "POST_GENERATION": ["PRE_GENERATION"],
        "PRE_TOOL": ["PRE_GENERATION", "POST_GENERATION"],
        "POST_TOOL": ["PRE_GENERATION", "POST_GENERATION", "PRE_TOOL"],
    }
    value = {
        "schema": "szl.nemo.inference-envelope.v1",
        "stage": stage,
        "witness_identity": {
            "artifact_kind": "SOFTWARE_KERNEL",
            "generative": False,
            "not_nemotron": True,
        },
        "scope": {
            "principal_id_sha256": DIGEST,
            "tenant_id_sha256": "f" * 64,
            "access_decision": "ALLOW",
            "policy_revision": POLICY_REV,
        },
        "model": {
            "id": "example/proposal-model",
            "revision": REV_A,
            "adapter_revision": "NONE",
            "tokenizer_revision": REV_B,
            "template_revision": REV_C,
        },
        "runtime": {
            "engine": "vllm",
            "version": "1.0.0",
            "hardware_fingerprint": "gpu:test",
        },
        "evidence": {
            "content_access": "HANDLES_ONLY",
            "grounding_required": True,
            "handles": [{"nodeId": "formula:locked-eight"}],
            "items": copy.deepcopy(EVIDENCE),
            "evidence_set_sha256": canonical_sha256(EVIDENCE),
        },
        "formulas": {
            "locked_proven_ids": list(LOCKED_EIGHT),
            "locked_proven_count": 8,
            "formal_source_repository": "szl-holdings/lutar-lean",
            "formal_source_commit": REV_A,
            "kernel_source_repository": "szl-holdings/szl-formulas",
            "kernel_source_commit": REV_B,
            "f_id_to_callable_mapping": "UNKNOWN_NOT_ASSERTED",
            "requested_formula_ids": ["F1"],
            "applications": [
                {
                    "formula_id": "F1",
                    "applicability": "APPLIES",
                    "basis_sha256": DIGEST,
                }
            ],
            "authorization_basis_ids": ["F1"],
            "lambda": {
                "formula_id": "F23",
                "status": "CONJECTURE_1_ADVISORY",
                "can_authorize": False,
                "can_be_sole_allow_basis": False,
            },
        },
        "authority": {
            "model_authority": "PROPOSAL_ONLY",
            "executed": stage == "POST_TOOL",
            "execution_authority": "A11OY" if stage == "POST_TOOL" else "NONE",
        },
        "witness_history": histories[stage],
        "claims": [{"label": "MEASURED", "statement_sha256": DIGEST}],
        "tool_intent": None,
        "action_admission": None,
        "receipt": None,
        "tool_result": None,
        "postcondition": None,
    }
    if stage == "PRE_TOOL":
        value["tool_intent"] = {"sha256": DIGEST}
        value["action_admission"] = {
            "authority": "A11OY",
            "human_approval": "PENDING",
            "signed_receipt_required": True,
        }
        value["receipt"] = {"signature_status": "UNSIGNED_HONEST"}
    elif stage == "POST_TOOL":
        value["tool_intent"] = {"sha256": DIGEST}
        value["action_admission"] = {
            "authority": "A11OY",
            "human_approval": "APPROVED",
            "signed_receipt_required": True,
        }
        value["receipt"] = {
            "signature_status": "SIGNED_VERIFIED",
            "sha256": DIGEST,
        }
        value["tool_result"] = {"sha256": DIGEST}
        value["postcondition"] = {
            "status": "PASS",
            "details_sha256": DIGEST,
        }
    return value


def test_valid_post_generation_is_allow_and_deterministic():
    first = evaluate_envelope(_envelope())
    second = evaluate_envelope(_envelope())
    assert first.decision == ALLOW
    assert first.to_json() == second.to_json()
    assert first.input_hash.startswith("sha256:")


def test_locked_five_drift_blocks():
    value = _envelope()
    value["formulas"]["locked_proven_ids"] = ["F1", "F11", "F12", "F18", "F19"]
    value["formulas"]["locked_proven_count"] = 5
    decision = evaluate_envelope(value)
    assert decision.decision == BLOCK
    assert "E4_formula_authority" in decision.violated_rules


def test_unproved_f_id_to_callable_mapping_blocks():
    value = _envelope()
    value["formulas"]["f_id_to_callable_mapping"] = "F1=lambda_aggregate"
    assert evaluate_envelope(value).decision == BLOCK


def test_formula_applicability_requires_bound_evidence():
    value = _envelope()
    value["formulas"]["applications"][0]["basis_sha256"] = "not-a-digest"
    assert evaluate_envelope(value).decision == BLOCK


def test_lambda_cannot_authorize():
    value = _envelope()
    value["formulas"]["lambda"]["can_authorize"] = True
    assert evaluate_envelope(value).decision == BLOCK


def test_lambda_cannot_enter_authorization_basis():
    value = _envelope()
    value["formulas"]["authorization_basis_ids"] = ["F23"]
    assert evaluate_envelope(value).decision == BLOCK


def test_denied_tenant_scope_blocks():
    value = _envelope()
    value["scope"]["access_decision"] = "DENY"
    assert evaluate_envelope(value).decision == BLOCK


def test_evidence_digest_tampering_blocks():
    value = _envelope()
    value["evidence"]["items"][0]["sha256"] = "0" * 64
    decision = evaluate_envelope(value)
    assert decision.decision == BLOCK
    assert "E3_scoped_evidence_binding" in decision.violated_rules


def test_handle_evidence_identity_mismatch_blocks():
    value = _envelope()
    value["evidence"]["handles"][0]["nodeId"] = "wrong-node"
    assert evaluate_envelope(value).decision == BLOCK


def test_mutable_model_revision_blocks():
    value = _envelope()
    value["model"]["revision"] = "main"
    assert evaluate_envelope(value).decision == BLOCK


def test_nemo_cannot_be_reclassified_as_nemotron():
    value = _envelope()
    value["witness_identity"]["generative"] = True
    value["witness_identity"]["not_nemotron"] = False
    assert evaluate_envelope(value).decision == BLOCK


def test_private_reasoning_key_blocks_and_is_not_returned():
    value = _envelope()
    value["metadata"] = {"chain_of_thought": "secret scratchpad"}
    decision = evaluate_envelope(value)
    assert decision.decision == BLOCK
    assert "E6_private_state_exclusion" in decision.violated_rules
    assert "secret scratchpad" not in decision.to_json()


def test_generation_stage_cannot_claim_execution():
    value = _envelope()
    value["authority"]["executed"] = True
    value["authority"]["execution_authority"] = "MODEL"
    assert evaluate_envelope(value).decision == BLOCK


def test_pre_tool_pending_human_approval_is_review():
    decision = evaluate_envelope(_envelope("PRE_TOOL"))
    assert decision.decision == REVIEW
    assert decision.violated_rules == ()


def test_pre_tool_approved_and_signed_is_allow_but_does_not_execute():
    value = _envelope("PRE_TOOL")
    value["action_admission"]["human_approval"] = "APPROVED"
    value["receipt"] = {"signature_status": "SIGNED_VERIFIED", "sha256": DIGEST}
    decision = evaluate_envelope(value)
    assert decision.decision == ALLOW
    assert value["authority"]["executed"] is False


def test_post_tool_requires_verified_signed_receipt():
    value = _envelope("POST_TOOL")
    value["receipt"]["signature_status"] = "UNSIGNED_HONEST"
    assert evaluate_envelope(value).decision == BLOCK


def test_post_tool_signed_pass_is_allow():
    assert evaluate_envelope(_envelope("POST_TOOL")).decision == ALLOW


def test_post_tool_failed_postcondition_is_review():
    value = _envelope("POST_TOOL")
    value["postcondition"]["status"] = "FAIL"
    assert evaluate_envelope(value).decision == REVIEW


def test_witness_stage_order_is_exact():
    value = _envelope()
    value["witness_history"] = []
    assert evaluate_envelope(value).decision == BLOCK


def test_unrecognized_truth_label_blocks():
    value = _envelope()
    value["claims"][0]["label"] = "PROVEN"
    assert evaluate_envelope(value).decision == BLOCK
