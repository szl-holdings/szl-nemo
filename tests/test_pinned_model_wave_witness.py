from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "frontier" / "pinned-model-wave-witness-2026-09-07.json"

EXPECTED_REVISIONS = {
    "zai-org/GLM-5.3-Flash": "eb9eb208eb0d988989d07a6a12d0fdeb5f52574a",
    "zai-org/GLM-5.3": "aca966e4e02791568aa6a4ced368624b3d897f42",
    "deepseek-ai/DeepSeek-V4-Flash-Vision-Exp": (
        "6821d6ad3681a4b137b066b76094fa82ebd0a380"
    ),
    "nvidia/Qwen3.8-Flash-Next-NVFP4": (
        "fc694b54fb0174e0913e6adf86691ef85a4ead47"
    ),
    "Qwen/Qwen3.8-Flash-Next": "de4b8e4d43b917e7706784d8bb445c9af86a3540",
}


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _candidates() -> dict[str, dict]:
    return {row["model_id"]: row for row in _contract()["candidate_identities"]}


def test_wave_witness_is_bound_to_frontier_and_forge_exact_heads() -> None:
    contract = _contract()
    upstream = contract["upstream_contracts"]
    assert contract["schema"] == "szl.frontier.nemo-model-wave-witness-envelope.v1"
    assert contract["default_effect"] == "HOLD"
    assert contract["evaluation_mode"] == "HELD_OUT_COMPARATIVE_WITNESS"
    assert (
        upstream["frontier_registry"]["revision"]
        == "dcc128140f3873d0ca396b9a83cf0eb5a0102b87"
    )
    assert (
        upstream["forge_qualification"]["revision"]
        == "ffe66a1aba2c6027e48da6f89cdd5d4fc2f87794"
    )
    for value in (
        upstream["frontier_registry"]["revision"],
        upstream["forge_qualification"]["revision"],
    ):
        assert re.fullmatch(r"[0-9a-f]{40}", value)


def test_nemo_retains_zero_training_routing_execution_or_promotion_authority() -> None:
    authorities = _contract()["authorities"]
    assert authorities == {
        "training": False,
        "routing": False,
        "execution": False,
        "production_promotion": False,
    }


def test_candidate_identities_match_the_forge_wave_exactly() -> None:
    candidates = _candidates()
    assert set(candidates) == set(EXPECTED_REVISIONS)
    for model_id, revision in EXPECTED_REVISIONS.items():
        candidate = candidates[model_id]
        assert candidate["revision"] == revision
        assert re.fullmatch(r"[0-9a-f]{40}", revision)
        assert candidate["promotion_effect"] == "NONE"
        assert candidate["results"] is None
        assert candidate["required_metrics"]


def test_review_required_artifacts_remain_on_license_hold() -> None:
    for candidate in _candidates().values():
        if candidate["declared_license"] == "other":
            assert candidate["license_posture"] == "REVIEW_REQUIRED"
            assert candidate["forge_evaluation_state"] == "LICENSE_REVIEW_REQUIRED"
            assert candidate["witness_status"] in {
                "LICENSE_AND_QUALIFICATION_HOLD",
                "REFERENCE_HOLD",
            }


def test_quantized_derivative_is_bound_to_its_base_revision() -> None:
    candidate = _candidates()["nvidia/Qwen3.8-Flash-Next-NVFP4"]
    assert candidate["base_model_id"] == "Qwen/Qwen3.8-Flash-Next"
    assert (
        candidate["base_model_revision"]
        == EXPECTED_REVISIONS["Qwen/Qwen3.8-Flash-Next"]
    )


def test_truth_labels_match_the_nemo_envelope_vocabulary() -> None:
    assert set(_contract()["truth_labels"]) == {
        "MEASURED",
        "REPORTED",
        "MODELED",
        "CONJECTURE",
        "UNKNOWN",
        "UNAVAILABLE",
    }


def test_receipt_requires_identity_results_fallback_and_decision_binding() -> None:
    receipt = _contract()["witness_receipt"]
    assert receipt["schema"] == "szl.nemo.frontier-qualification-receipt.v1"
    assert receipt["evidence_complete_decision"] == (
        "EVIDENCE_COMPLETE_REVIEW_REQUIRED"
    )
    assert receipt["incomplete_or_failed_decision"] == "HOLD"
    assert receipt["promotion_effect"] == "NONE"
    assert {
        "candidate_id",
        "model_id",
        "model_revision",
        "tokenizer_revision",
        "template_revision",
        "runtime_engine",
        "runtime_version",
        "hardware_fingerprint",
        "software_fingerprint",
        "fixture_set_sha256",
        "configuration_sha256",
        "seed",
        "baseline_results_sha256",
        "candidate_results_sha256",
        "metric_truth_labels",
        "violated_invariants",
        "fallback_evidence_sha256",
        "decision",
        "receipt_sha256",
    } <= set(receipt["required_fields"])


def test_global_invariants_are_fail_closed_and_authority_bounded() -> None:
    invariants = " ".join(_contract()["global_invariants"]).lower()
    for required in {
        "checksum-pinned held-out fixtures",
        "proposal only",
        "a11oy remains the sole consequential-action admission layer",
        "never converted into a pass",
        "baseline fallback",
        "license compatibility",
        "remote-code review",
        "cannot promote a model",
    }:
        assert required in invariants
