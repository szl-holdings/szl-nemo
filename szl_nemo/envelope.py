# SPDX-License-Identifier: Apache-2.0
"""Deterministic witness for structured, proof-carrying inference envelopes.

This module is stdlib-only and non-generative. It inspects identities, authority
states, and digests; it never loads weights, retrieves content, executes tools,
or grants action authority. Existing prompt/answer R1-R5 evaluation is preserved.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, Iterable, List, Tuple

from .schema import ALLOW, BLOCK, REVIEW, Decision

ENVELOPE_SCHEMA_VERSION = "szl.nemo.inference-envelope.v1"
ENVELOPE_RULE_VERSION = "doctrine-v11/E1-E10"
ENVELOPE_RULE_IDS = (
    "E1_envelope_identity",
    "E2_pinned_model_runtime_identity",
    "E3_scoped_evidence_binding",
    "E4_formula_authority",
    "E5_execution_authority",
    "E6_private_state_exclusion",
    "E7_tool_admission",
    "E8_witness_stage_order",
    "E9_postcondition_binding",
    "E10_truth_label_binding",
)
LOCKED_PROVEN_FORMULA_IDS = (
    "F1",
    "F4",
    "F7",
    "F11",
    "F12",
    "F18",
    "F19",
    "F22",
)
TRUTH_LABELS = frozenset(
    {"MEASURED", "REPORTED", "MODELED", "CONJECTURE", "UNKNOWN", "UNAVAILABLE"}
)
STAGES = ("PRE_GENERATION", "POST_GENERATION", "PRE_TOOL", "POST_TOOL")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})$")
FORBIDDEN_KEYS = frozenset(
    {
        "prompt",
        "raw_prompt",
        "answer",
        "raw_answer",
        "content",
        "raw_content",
        "hydrated_content",
        "chain_of_thought",
        "private_chain_of_thought",
        "hidden_reasoning",
        "reasoning_trace",
        "raw_private_graph",
        "private_graph",
        "private_graph_nodes",
    }
)

_RULE_REASONS = {
    "E1_envelope_identity": (
        "envelope schema or Nemo non-generative witness identity is invalid"
    ),
    "E2_pinned_model_runtime_identity": (
        "model, adapter, tokenizer, template, runtime, or hardware identity is "
        "missing or mutable"
    ),
    "E3_scoped_evidence_binding": (
        "principal/tenant scope, Second Brain handles, source digests, or the "
        "evidence-set digest do not bind"
    ),
    "E4_formula_authority": (
        "formal formula authority, locked-eight invariant, applicability evidence, "
        "namespace separation, or Lambda advisory status drifted"
    ),
    "E5_execution_authority": (
        "the proposal-only model crossed or obscured the A11oy execution boundary"
    ),
    "E6_private_state_exclusion": (
        "raw content, private graph state, or private reasoning appears in the envelope"
    ),
    "E7_tool_admission": (
        "tool intent lacks A11oy admission, required human approval, or a verified "
        "signed receipt"
    ),
    "E8_witness_stage_order": (
        "required prior witness stages are missing, duplicated, or out of order"
    ),
    "E9_postcondition_binding": (
        "tool result or postcondition evidence is missing, malformed, or unbound"
    ),
    "E10_truth_label_binding": (
        "a persisted claim lacks an allowed truth label or statement digest"
    ),
}


def canonical_bytes(value: Any) -> bytes:
    """Return canonical UTF-8 JSON bytes used by every envelope digest."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return a lowercase SHA-256 digest of canonical JSON bytes."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def envelope_input_hash(envelope: Mapping[str, Any]) -> str:
    """Hash the complete envelope deterministically."""
    if not isinstance(envelope, Mapping):
        raise TypeError("envelope must be a mapping")
    return "sha256:" + canonical_sha256(dict(envelope))


def _is_hex64(value: Any) -> bool:
    return bool(HEX64.fullmatch(str(value or "").lower()))


def _is_pinned(value: Any, *, allow_none: bool = False) -> bool:
    token = str(value or "").strip().lower()
    if allow_none and token == "none":
        return True
    return bool(REVISION.fullmatch(token))


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key).lower()
            yield from _walk_keys(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _walk_keys(item)


def _rule_e1(envelope: Mapping[str, Any]) -> bool:
    identity = _mapping(envelope.get("witness_identity"))
    return (
        envelope.get("schema") == ENVELOPE_SCHEMA_VERSION
        and envelope.get("stage") in STAGES
        and identity.get("artifact_kind") == "SOFTWARE_KERNEL"
        and identity.get("generative") is False
        and identity.get("not_nemotron") is True
    )


def _rule_e2(envelope: Mapping[str, Any]) -> bool:
    model = _mapping(envelope.get("model"))
    runtime = _mapping(envelope.get("runtime"))
    return (
        bool(str(model.get("id") or "").strip())
        and _is_pinned(model.get("revision"))
        and _is_pinned(model.get("adapter_revision"), allow_none=True)
        and _is_pinned(model.get("tokenizer_revision"))
        and _is_pinned(model.get("template_revision"))
        and bool(str(runtime.get("engine") or "").strip())
        and bool(str(runtime.get("version") or "").strip())
        and bool(str(runtime.get("hardware_fingerprint") or "").strip())
    )


def _rule_e3(envelope: Mapping[str, Any]) -> bool:
    scope = _mapping(envelope.get("scope"))
    evidence = _mapping(envelope.get("evidence"))
    if not (
        _is_hex64(scope.get("principal_id_sha256"))
        and _is_hex64(scope.get("tenant_id_sha256"))
        and scope.get("access_decision") == "ALLOW"
        and _is_pinned(scope.get("policy_revision"))
    ):
        return False
    if evidence.get("content_access") != "HANDLES_ONLY":
        return False
    if not isinstance(evidence.get("grounding_required"), bool):
        return False
    handles = list(_sequence(evidence.get("handles")))
    items = list(_sequence(evidence.get("items")))
    if evidence.get("grounding_required") and not items:
        return False
    handle_ids: List[str] = []
    item_ids: List[str] = []
    for raw in handles:
        if not isinstance(raw, Mapping):
            return False
        node_id = str(raw.get("nodeId") or "")
        if not node_id:
            return False
        handle_ids.append(node_id)
    for raw in items:
        if not isinstance(raw, Mapping):
            return False
        node_id = str(raw.get("node_id") or "")
        source = str(raw.get("source") or "")
        digest = str(raw.get("sha256") or "").lower()
        if not node_id or not source or not _is_hex64(digest):
            return False
        item_ids.append(node_id)
    if len(handle_ids) != len(set(handle_ids)):
        return False
    if len(item_ids) != len(set(item_ids)):
        return False
    if handle_ids != item_ids:
        return False
    declared = str(evidence.get("evidence_set_sha256") or "").lower()
    return declared == canonical_sha256(items)


def _rule_e4(envelope: Mapping[str, Any]) -> bool:
    formulas = _mapping(envelope.get("formulas"))
    requested = tuple(
        str(value) for value in _sequence(formulas.get("requested_formula_ids"))
    )
    authorization_basis = tuple(
        str(value) for value in _sequence(formulas.get("authorization_basis_ids"))
    )
    applications = list(_sequence(formulas.get("applications")))
    application_ids: List[str] = []
    for application in applications:
        if not isinstance(application, Mapping):
            return False
        formula_id = str(application.get("formula_id") or "")
        if (
            not formula_id
            or application.get("applicability") != "APPLIES"
            or not _is_hex64(application.get("basis_sha256"))
        ):
            return False
        application_ids.append(formula_id)
    allowed = set(LOCKED_PROVEN_FORMULA_IDS) | {"F23"}
    lambda_rule = _mapping(formulas.get("lambda"))
    return (
        tuple(formulas.get("locked_proven_ids") or ())
        == LOCKED_PROVEN_FORMULA_IDS
        and formulas.get("locked_proven_count") == 8
        and formulas.get("formal_source_repository") == "szl-holdings/lutar-lean"
        and _is_pinned(formulas.get("formal_source_commit"))
        and formulas.get("kernel_source_repository") == "szl-holdings/szl-formulas"
        and _is_pinned(formulas.get("kernel_source_commit"))
        and formulas.get("f_id_to_callable_mapping") == "UNKNOWN_NOT_ASSERTED"
        and len(requested) == len(set(requested))
        and set(requested).issubset(allowed)
        and tuple(application_ids) == requested
        and len(authorization_basis) == len(set(authorization_basis))
        and set(authorization_basis).issubset(set(LOCKED_PROVEN_FORMULA_IDS))
        and lambda_rule.get("formula_id") == "F23"
        and lambda_rule.get("status") == "CONJECTURE_1_ADVISORY"
        and lambda_rule.get("can_authorize") is False
        and lambda_rule.get("can_be_sole_allow_basis") is False
    )


def _rule_e5(envelope: Mapping[str, Any]) -> bool:
    authority = _mapping(envelope.get("authority"))
    stage = envelope.get("stage")
    if authority.get("model_authority") != "PROPOSAL_ONLY":
        return False
    executed = authority.get("executed")
    execution_authority = authority.get("execution_authority")
    if stage == "POST_TOOL":
        return executed is True and execution_authority == "A11OY"
    return executed is False and execution_authority in (None, "NONE")


def _rule_e6(envelope: Mapping[str, Any]) -> bool:
    return not (set(_walk_keys(envelope)) & FORBIDDEN_KEYS)


def _tool_parts(
    envelope: Mapping[str, Any],
) -> Tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    return (
        _mapping(envelope.get("tool_intent")),
        _mapping(envelope.get("action_admission")),
        _mapping(envelope.get("receipt")),
    )


def _rule_e7(envelope: Mapping[str, Any]) -> bool:
    stage = envelope.get("stage")
    tool, admission, receipt = _tool_parts(envelope)
    if stage in ("PRE_GENERATION", "POST_GENERATION"):
        return not tool and not admission
    if not _is_hex64(tool.get("sha256")):
        return False
    if (
        admission.get("authority") != "A11OY"
        or admission.get("signed_receipt_required") is not True
        or admission.get("human_approval") not in {"PENDING", "APPROVED"}
    ):
        return False
    if stage == "PRE_TOOL" and admission.get("human_approval") == "PENDING":
        return receipt.get("signature_status") in {"UNSIGNED_HONEST", "PENDING"}
    return (
        admission.get("human_approval") == "APPROVED"
        and receipt.get("signature_status") == "SIGNED_VERIFIED"
        and _is_hex64(receipt.get("sha256"))
    )


def _rule_e8(envelope: Mapping[str, Any]) -> bool:
    stage = str(envelope.get("stage") or "")
    history = [str(value) for value in _sequence(envelope.get("witness_history"))]
    if len(history) != len(set(history)):
        return False
    if any(value not in STAGES for value in history):
        return False
    required = {
        "PRE_GENERATION": [],
        "POST_GENERATION": ["PRE_GENERATION"],
        "PRE_TOOL": ["PRE_GENERATION", "POST_GENERATION"],
        "POST_TOOL": ["PRE_GENERATION", "POST_GENERATION", "PRE_TOOL"],
    }.get(stage, [])
    return history == required


def _rule_e9(envelope: Mapping[str, Any]) -> bool:
    stage = envelope.get("stage")
    postcondition = _mapping(envelope.get("postcondition"))
    result = _mapping(envelope.get("tool_result"))
    if stage != "POST_TOOL":
        return not postcondition and not result
    return (
        _is_hex64(result.get("sha256"))
        and postcondition.get("status") in {"PASS", "FAIL"}
        and _is_hex64(postcondition.get("details_sha256"))
    )


def _rule_e10(envelope: Mapping[str, Any]) -> bool:
    claims = envelope.get("claims")
    if not isinstance(claims, list):
        return False
    for claim in claims:
        if not isinstance(claim, Mapping):
            return False
        if claim.get("label") not in TRUTH_LABELS:
            return False
        if not _is_hex64(claim.get("statement_sha256")):
            return False
    return True


_RULES = (
    (ENVELOPE_RULE_IDS[0], _rule_e1),
    (ENVELOPE_RULE_IDS[1], _rule_e2),
    (ENVELOPE_RULE_IDS[2], _rule_e3),
    (ENVELOPE_RULE_IDS[3], _rule_e4),
    (ENVELOPE_RULE_IDS[4], _rule_e5),
    (ENVELOPE_RULE_IDS[5], _rule_e6),
    (ENVELOPE_RULE_IDS[6], _rule_e7),
    (ENVELOPE_RULE_IDS[7], _rule_e8),
    (ENVELOPE_RULE_IDS[8], _rule_e9),
    (ENVELOPE_RULE_IDS[9], _rule_e10),
)


def envelope_check(envelope: Mapping[str, Any]) -> Tuple[bool, List[str]]:
    """Return ``(ok, violated_rule_ids)`` for a JSON-compatible mapping."""
    if not isinstance(envelope, Mapping):
        raise TypeError("envelope must be a mapping")
    violated: List[str] = []
    for rule_id, check in _RULES:
        try:
            passed = bool(check(envelope))
        except (TypeError, ValueError, OverflowError):
            passed = False
        if not passed:
            violated.append(rule_id)
    return not violated, violated


def evaluate_envelope(envelope: Mapping[str, Any]) -> Decision:
    """Evaluate one structured inference stage without executing its tool intent.

    A valid PRE_TOOL with pending human approval returns REVIEW. A valid POST_TOOL
    whose bound postcondition is FAIL also returns REVIEW. Any structural,
    provenance, privacy, or authority drift returns BLOCK.
    """
    ok, violated = envelope_check(envelope)
    digest = envelope_input_hash(envelope)
    if not ok:
        return Decision(
            decision=BLOCK,
            violated_rules=tuple(violated),
            rule_version=ENVELOPE_RULE_VERSION,
            input_hash=digest,
            reasons=tuple(_RULE_REASONS[rule] for rule in violated),
        )
    stage = envelope.get("stage")
    admission = _mapping(envelope.get("action_admission"))
    postcondition = _mapping(envelope.get("postcondition"))
    if stage == "PRE_TOOL" and admission.get("human_approval") == "PENDING":
        return Decision(
            decision=REVIEW,
            violated_rules=(),
            rule_version=ENVELOPE_RULE_VERSION,
            input_hash=digest,
            reasons=(
                "A11oy human approval and a verified signed receipt are pending; "
                "no tool was executed",
            ),
        )
    if stage == "POST_TOOL" and postcondition.get("status") == "FAIL":
        return Decision(
            decision=REVIEW,
            violated_rules=(),
            rule_version=ENVELOPE_RULE_VERSION,
            input_hash=digest,
            reasons=(
                "the A11oy-admitted tool action executed but its bound postcondition failed",
            ),
        )
    return Decision(
        decision=ALLOW,
        violated_rules=(),
        rule_version=ENVELOPE_RULE_VERSION,
        input_hash=digest,
        reasons=(),
    )


__all__ = [
    "ENVELOPE_RULE_IDS",
    "ENVELOPE_RULE_VERSION",
    "ENVELOPE_SCHEMA_VERSION",
    "LOCKED_PROVEN_FORMULA_IDS",
    "STAGES",
    "TRUTH_LABELS",
    "canonical_sha256",
    "envelope_check",
    "envelope_input_hash",
    "evaluate_envelope",
]
