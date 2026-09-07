from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "frontier" / "hf-top-choice-2026-09-07.json"


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_nemo_frontier_binding_has_no_production_authority() -> None:
    contract = _contract()
    assert contract["schema"] == "szl.frontier.nemo-witness-binding.v1"
    assert contract["default_effect"] == "HOLD"
    assert contract["canonical_frontier_revision"] == "94a039d086d1343d1fcfe5bca617f601006ca05b"
    assert contract["serve_contract_revision"] == "74c2fa12ee3cd17cc8d80ac85801f11683912176"
    assert contract["training_authority"] is False
    assert contract["routing_authority"] is False
    assert contract["execution_authority"] is False
    assert contract["production_promotion"] is False


def test_k2_witness_requires_agent_tool_context_and_policy_evidence() -> None:
    candidates = {row["id"]: row for row in _contract()["candidates"]}
    k2 = candidates["k2-horizon-mova-36b-a4b-2026-09-03"]
    assert k2["status"] == "QUALIFICATION_REQUIRED"
    assert k2["source_revision"] == "05cab0a4d7150c1c460a000b37ff40cc1af2feaa"
    assert k2["artifact_fingerprint"] == "259e31e5a7143d4f6cca70ed238296e9374b0a51aa497563f62e10af990ec9e2"
    metrics = set(k2["required_metrics"])
    assert {
        "agent_task_success_rate",
        "tool_call_exact_match",
        "schema_exact_match",
        "long_context_grounded_recall",
        "unsupported_claim_rate",
        "refusal_and_policy_regression_rate",
    }.issubset(metrics)
    invariants = " ".join(k2["required_invariants"]).lower()
    assert "proposals only" in invariants
    assert "canaries never cross" in invariants
    assert "never converted into a pass" in invariants
    assert k2["promotion_effect"] == "NONE"


def test_vaani_stays_gated_until_authorized_access() -> None:
    candidates = {row["id"]: row for row in _contract()["candidates"]}
    vaani = candidates["vaani-noise-event-2026-08-07"]
    assert vaani["status"] == "GATED_HOLD"
    invariants = " ".join(vaani["required_invariants"]).lower()
    assert "no dataset payload is fetched before authorized hugging face gate acceptance" in invariants
    assert "checksum-pinned bounded samples" in invariants
    assert "voice-clone objectives remain out of scope" in invariants
    assert vaani["promotion_effect"] == "NONE"
