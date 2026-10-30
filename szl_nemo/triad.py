# SPDX-License-Identifier: Apache-2.0
"""Bind one governed witness across the Nemo, NVIDIA, and DARPA surfaces.

Stdlib only. This module does not load weights, call NVML, sign a DSSE
envelope, or grant tool authority. A caller supplies digests and a joule
figure. The binder checks the shape and stamps the citations.

Unconditional Λ uniqueness under axioms A1–A5 is machine-checked false as
stated in szl-holdings/lutar-lean (maxAgg and min meet A1–A5 and are not Λ).
Theorem U is conditional. The score computed here is a modeled geometric
mean. One zero axis forces 0. It is not a proof and not an authorization.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Tuple

from .schema import ALLOW, BLOCK

TRIAD_SCHEMA = "szl.nemo.triad.v1"
TRIAD_RULE_VERSION = "doctrine-v11/triad-v1"
LAMBDA_STATUS_LABEL = (
    "Λ = Conjecture 1 — unconditional uniqueness false as stated "
    "(maxAgg); Theorem U conditional; never authorization"
)
LEAN_REPOSITORY = "szl-holdings/lutar-lean"
LEAN_COMMIT = "990526e23d6d35a7b4109a8b67b171b0af3785ce"
RECEIPT_STATUS = "UNSIGNED_HONEST"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_REVISION = re.compile(r"^(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})$")
_WEIGHT_SUM_TOLERANCE = 1e-9
_TOP_KEYS = frozenset({"authorization", "proposal", "energy", "lambda"})
_AUTH_KEYS = frozenset(
    {
        "principal_id_sha256",
        "tenant_id_sha256",
        "access_decision",
        "policy_revision",
        "request_sha256",
    }
)
_PROPOSAL_KEYS = frozenset(
    {
        "family",
        "authority",
        "output_sha256",
        "model_id",
        "model_revision",
    }
)
_ENERGY_KEYS = frozenset({"joules", "label", "source"})
_LAMBDA_KEYS = frozenset({"scores", "weights"})
_FAMILIES = frozenset({"NVIDIA_NEMOTRON", "OTHER"})
_FORBIDDEN_KEYS = frozenset(
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
        "signature",
        "dsse",
        "envelope",
    }
)

DARPA_BOUNDARY = {
    "szl_award": "NONE_ASSERTED",
    "public_programs": ["ANSR", "ARCOS", "CLARA"],
    "note": (
        "Public program pages are references. This record is not a DARPA "
        "award, a measurement of those programs, or a signature."
    ),
}
NVIDIA_BOUNDARY = {
    "role": "PROPOSAL_ONLY",
    "witness_is_not_the_model": True,
    "note": (
        "An NVIDIA Nemotron reply is a proposal. szl-nemo does not load "
        "those weights and does not republish them."
    ),
}


@dataclass(frozen=True)
class TriadDecision:
    """One unsigned triad record. ``body_json`` is canonical."""

    decision: str
    reasons: Tuple[str, ...]
    body_json: str
    rule_version: str = TRIAD_RULE_VERSION

    def record(self) -> dict:
        loaded = json.loads(self.body_json)
        if not isinstance(loaded, dict):
            raise TypeError("triad record must be an object")
        return loaded


def strict_json_loads(text: str) -> Any:
    """Parse JSON and reject non-finite numbers and duplicate keys."""

    def parse_float(token: str) -> float:
        value = float(token)
        if not math.isfinite(value):
            raise ValueError("non-finite number")
        return value

    def parse_constant(token: str) -> Any:
        raise ValueError(f"non-finite constant {token}")

    def pairs(items: List[Tuple[str, Any]]) -> dict:
        obj: dict = {}
        for key, value in items:
            if key in obj:
                raise ValueError(f"duplicate key {key}")
            obj[key] = value
        return obj

    return json.loads(
        text,
        parse_float=parse_float,
        parse_constant=parse_constant,
        object_pairs_hook=pairs,
    )


def geometric_mean(
    scores: Sequence[float], weights: Optional[Sequence[float]] = None
) -> float:
    """Weighted geometric mean on (0, 1]. A zero score returns 0.

    Callers must already have rejected non-finite values, bools, empty
    input, and weights that are not strictly positive and do not sum to 1.
    """
    if any(score == 0.0 for score in scores):
        return 0.0
    if weights is None:
        scale = 1.0 / len(scores)
        weights = [scale] * len(scores)
    return math.exp(
        sum(weight * math.log(score) for weight, score in zip(weights, scores))
    )


def _canonical(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key).lower()
            yield from _walk_keys(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _walk_keys(item)


def _hex64(value: Any) -> Optional[str]:
    token = str(value or "").strip().lower()
    if _HEX64.fullmatch(token):
        return token
    return None


def _revision(value: Any) -> Optional[str]:
    token = str(value or "").strip().lower()
    if _REVISION.fullmatch(token):
        return token
    return None


def _real(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _unknown_keys(value: Mapping[str, Any], allowed: frozenset) -> List[str]:
    return sorted(str(key) for key in value.keys() if key not in allowed)


def evaluate_triad(document: Mapping[str, Any]) -> TriadDecision:
    """Check one triad document and return an unsigned record.

    ALLOW means the document has the required shape. It does not execute a
    model, verify a signature, or authorize a tool.
    """
    if not isinstance(document, Mapping):
        raise TypeError("triad document must be a mapping")

    reasons: List[str] = []
    if set(_walk_keys(document)) & _FORBIDDEN_KEYS:
        reasons.append(
            "raw content, private reasoning, or a signature field is present"
        )
    unknown = _unknown_keys(document, _TOP_KEYS)
    if unknown:
        reasons.append("unknown top-level fields: " + ",".join(unknown))

    authorization = _mapping(document.get("authorization"))
    proposal = _mapping(document.get("proposal"))
    energy = _mapping(document.get("energy"))
    lambda_doc = _mapping(document.get("lambda"))
    if not isinstance(document.get("authorization"), Mapping):
        reasons.append("authorization must be an object")
    if not isinstance(document.get("proposal"), Mapping):
        reasons.append("proposal must be an object")
    if not isinstance(document.get("energy"), Mapping):
        reasons.append("energy must be an object")
    if not isinstance(document.get("lambda"), Mapping):
        reasons.append("lambda must be an object")

    reasons.extend(_check_authorization(authorization))
    reasons.extend(_check_proposal(proposal))
    energy_out, energy_reasons = _check_energy(energy)
    reasons.extend(energy_reasons)
    score, lambda_reasons = _check_lambda(lambda_doc)
    reasons.extend(lambda_reasons)

    decision = BLOCK if reasons else ALLOW
    body = {
        "schema": TRIAD_SCHEMA,
        "witness_identity": {
            "artifact": "szl-nemo",
            "artifact_kind": "SOFTWARE_KERNEL",
            "generative": False,
            "not_nemotron": True,
        },
        "authorization": {
            "principal_id_sha256": _hex64(authorization.get("principal_id_sha256")),
            "tenant_id_sha256": _hex64(authorization.get("tenant_id_sha256")),
            "access_decision": authorization.get("access_decision"),
            "policy_revision": _revision(authorization.get("policy_revision")),
            "request_sha256": _hex64(authorization.get("request_sha256")),
        },
        "proposal": {
            "family": proposal.get("family"),
            "authority": proposal.get("authority"),
            "output_sha256": _hex64(proposal.get("output_sha256")),
            "model_id": proposal.get("model_id"),
            "model_revision": _revision(proposal.get("model_revision")),
        },
        "energy": energy_out,
        "lambda": {
            "formula_id": "F23",
            "score": score,
            "score_label": "MODELED" if score is not None else "UNAVAILABLE",
            "status_label": LAMBDA_STATUS_LABEL,
            "unconditional_uniqueness": "FALSE_AS_STATED",
            "counterexample": "Lutar.Round13.maxAgg_ne_Lambda",
            "conditional_theorem": "TheoremU_LambdaUnique",
            "can_authorize": False,
            "formal_source_repository": LEAN_REPOSITORY,
            "formal_source_commit": LEAN_COMMIT,
        },
        "nvidia": NVIDIA_BOUNDARY,
        "darpa": DARPA_BOUNDARY,
        "dsse": None,
        "receipt_status": RECEIPT_STATUS,
        "decision": decision,
        "reasons": list(reasons),
    }
    body["record_sha256"] = _sha256(body)
    return TriadDecision(
        decision=decision,
        reasons=tuple(reasons),
        body_json=_canonical(body),
    )


def _check_authorization(authorization: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    unknown = _unknown_keys(authorization, _AUTH_KEYS)
    if unknown:
        reasons.append("unknown authorization fields: " + ",".join(unknown))
    if _hex64(authorization.get("principal_id_sha256")) is None:
        reasons.append("principal_id_sha256 is not 64 hex characters")
    if _hex64(authorization.get("tenant_id_sha256")) is None:
        reasons.append("tenant_id_sha256 is not 64 hex characters")
    if _hex64(authorization.get("request_sha256")) is None:
        reasons.append("request_sha256 is not 64 hex characters")
    if _revision(authorization.get("policy_revision")) is None:
        reasons.append("policy_revision is not a pinned revision")
    if authorization.get("access_decision") != "ALLOW":
        reasons.append("caller is not authorized")
    return reasons


def _check_proposal(proposal: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    unknown = _unknown_keys(proposal, _PROPOSAL_KEYS)
    if unknown:
        reasons.append("unknown proposal fields: " + ",".join(unknown))
    if proposal.get("family") not in _FAMILIES:
        reasons.append("proposal family is not NVIDIA_NEMOTRON or OTHER")
    if proposal.get("authority") != "PROPOSAL_ONLY":
        reasons.append("model authority is not PROPOSAL_ONLY")
    if _hex64(proposal.get("output_sha256")) is None:
        reasons.append("proposal output_sha256 is not 64 hex characters")
    model_id = proposal.get("model_id")
    if not isinstance(model_id, str) or not model_id.strip() or any(
        char in model_id for char in "\r\n"
    ):
        reasons.append("model_id is missing")
    if _revision(proposal.get("model_revision")) is None:
        reasons.append("model_revision is not a pinned revision")
    return reasons


def _check_energy(energy: Mapping[str, Any]) -> Tuple[dict, List[str]]:
    reasons: List[str] = []
    unknown = _unknown_keys(energy, _ENERGY_KEYS)
    if unknown:
        reasons.append("unknown energy fields: " + ",".join(unknown))
    label = energy.get("label")
    source = energy.get("source")
    joules = energy.get("joules")
    if label == "MEASURED" and source == "NVML":
        number = _real(joules)
        if number is None or number < 0.0:
            reasons.append("MEASURED energy needs a finite non-negative joule value")
            return {"joules": None, "label": "UNAVAILABLE", "source": source}, reasons
        return {"joules": number, "label": "MEASURED", "source": "NVML"}, reasons
    if label == "UNAVAILABLE" and source == "NVML_ABSENT" and joules is None:
        return {"joules": None, "label": "UNAVAILABLE", "source": "NVML_ABSENT"}, reasons
    reasons.append("energy must be NVML joules or an honest null")
    return {"joules": None, "label": "UNAVAILABLE", "source": source}, reasons


def _check_lambda(lambda_doc: Mapping[str, Any]) -> Tuple[Optional[float], List[str]]:
    reasons: List[str] = []
    unknown = _unknown_keys(lambda_doc, _LAMBDA_KEYS)
    if unknown:
        reasons.append("unknown lambda fields: " + ",".join(unknown))
    if lambda_doc.get("can_authorize") is True or lambda_doc.get("proven") is True:
        reasons.append("lambda cannot authorize and is not proven")
    raw_scores = lambda_doc.get("scores")
    if not isinstance(raw_scores, list) or not raw_scores:
        reasons.append("lambda scores must be a non-empty list")
        return None, reasons
    scores: List[float] = []
    for item in raw_scores:
        number = _real(item)
        if number is None or number < 0.0 or number > 1.0:
            reasons.append("each lambda score must be finite and inside [0, 1]")
            return None, reasons
        scores.append(number)
    raw_weights = lambda_doc.get("weights")
    weights: Optional[List[float]] = None
    if raw_weights is not None:
        if not isinstance(raw_weights, list) or len(raw_weights) != len(scores):
            reasons.append("lambda weights must match the score count")
            return None, reasons
        weights = []
        for item in raw_weights:
            number = _real(item)
            if number is None or number <= 0.0:
                reasons.append("each lambda weight must be finite and positive")
                return None, reasons
            weights.append(number)
        if abs(math.fsum(weights) - 1.0) > _WEIGHT_SUM_TOLERANCE:
            reasons.append("lambda weights must sum to 1")
            return None, reasons
    return geometric_mean(scores, weights), reasons
