from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WITNESS = (
    ROOT
    / "frontier"
    / "glm-5-3-flash-evaluation-witness.v1.json"
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load() -> dict:
    return json.loads(WITNESS.read_text(encoding="utf-8"))


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_witness_is_content_addressed() -> None:
    value = load()
    asserted = value["witness_receipt_sha256"]
    payload = {
        key: item
        for key, item in value.items()
        if key != "witness_receipt_sha256"
    }
    assert HEX64.fullmatch(asserted)
    assert canonical_sha256(payload) == asserted


def test_witness_binds_exact_forge_and_hub_evidence() -> None:
    value = load()
    forge = value["forge_evidence"]
    hub = value["hugging_face_evidence"]
    assert value["schema"] == "szl.nemo.frontier-evaluation-witness.v1"
    assert forge["repository"] == "szl-holdings/szl-forge"
    assert forge["commit"] == "225751bcf16372360df9ad04d63cba39fc8bc0ca"
    assert HEX40.fullmatch(forge["commit"])
    assert HEX64.fullmatch(forge["artifact_sha256"])
    assert hub["dataset_id"] == "SZLHOLDINGS/szl-frontier-evaluation-receipts"
    assert HEX40.fullmatch(hub["commit"])
    assert HEX64.fullmatch(hub["subject_receipt_sha256"])
    assert HEX64.fullmatch(hub["receipt_file_sha256"])


def test_witness_attests_measured_evidence_and_semantic_fallback() -> None:
    value = load()
    checks = value["witness_checks"]
    assert checks["immutable_candidate_source_identity"] is True
    assert checks["candidate_and_baseline_calls_completed"] is True
    assert checks["candidate_schema_valid_rate"] == 1.0
    assert checks["candidate_score_rate"] == 0.916667
    assert checks["baseline_score_rate"] == 0.416667
    assert checks["measured_score_delta"] == 0.5
    assert checks["fallback_transport_pass"] is True
    assert checks["fallback_semantic_safety_pass"] is True
    assert checks["fallback_selected_source"] == (
        "DETERMINISTIC_SAFETY_GUARD"
    )
    assert checks["fallback_production_authority"] == "NONE"
    labels = value["truth_labels"]
    assert labels["request_response_metrics"] == "MEASURED"
    assert labels["provider_execution_revision"] == "UNAVAILABLE"
    assert labels["receipt_authenticity"] == "UNESTABLISHED"


def test_nemo_witness_never_grants_runtime_or_promotion_authority() -> None:
    value = load()
    assert value["authorities"] == {
        "execution": False,
        "production_promotion": False,
        "routing": False,
        "training": False,
    }
    assert value["decision"] == "EVIDENCE_COMPLETE_REVIEW_REQUIRED"
    assert value["production_disposition"] == "HOLD"
    assert value["promotion_effect"] == "NONE"
    assert value["signature_status"] == "UNSIGNED_HONEST"
    assert value["authenticity_not_established"] is True
    assert "integrity_receipt_is_unsigned" in value["known_bounds"]
