# SPDX-License-Identifier: Apache-2.0
"""Typed contract for szl-nemo doctrine decisions.

This module defines the wire shape of a doctrine decision. It is SOFTWARE:
deterministic, stdlib-only, and never loads joblib/pickle. It is not an LLM,
not Nemotron, and not a CUDA kernel.

Canonical JSON (sorted keys, tight separators, UTF-8) is the only hashing
surface. Any verifier can recompute input_sha256 from prompt + answer alone.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

RULE_VERSION = "doctrine-v11"
DECISION_SCHEMA = "szl.nemo-doctrine-decision/v1"
RECEIPT_SCHEMA = "szl.nemo-doctrine-receipt/v1"

ALLOW = "ALLOW"
BLOCK = "BLOCK"
REVIEW = "REVIEW"
DECISIONS = (ALLOW, BLOCK, REVIEW)

UNSIGNED_HONEST = "UNSIGNED_HONEST"

_RULE_ID_RE = re.compile(r"^R[1-5]_[a-z0-9_]+$")


def canonical_json(payload: Dict[str, Any]) -> bytes:
    """Canonical byte form for hashing and verification."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(payload: Dict[str, Any]) -> str:
    """SHA-256 over the canonical JSON form, prefixed per OCI digest style."""
    return "sha256:" + hashlib.sha256(canonical_json(payload)).hexdigest()


@dataclass(frozen=True)
class RuleCheckInput:
    """A single doctrine conformance question over one prompt/answer pair."""

    prompt: str
    answer: str

    def validate(self) -> List[str]:
        problems: List[str] = []
        if not isinstance(self.prompt, str) or not isinstance(self.answer, str):
            problems.append("prompt and answer must be strings")
        elif not self.prompt.strip() or not self.answer.strip():
            # An empty exchange carries no doctrine signal; it must be
            # reviewed rather than silently allowed.
            problems.append("prompt and answer must both be non-empty")
        return problems

    def payload(self) -> Dict[str, str]:
        return {"prompt": self.prompt, "answer": self.answer}

    def digest(self) -> str:
        return sha256_hex(self.payload())


@dataclass(frozen=True)
class Decision:
    """The deterministic outcome of evaluating one RuleCheckInput."""

    decision: str
    reasons: List[str]
    violated_rules: List[str]
    input_sha256: str
    rule_version: str = RULE_VERSION
    engine: Dict[str, str] = field(
        default_factory=lambda: {
            "name": "szl_nemo.rule_check",
            "kind": "deterministic-python-stdlib",
        }
    )
    receipt_status: str = UNSIGNED_HONEST
    schema_name: str = DECISION_SCHEMA

    def payload(self) -> Dict[str, Any]:
        return {
            "schema": self.schema_name,
            "rule_version": self.rule_version,
            "decision": self.decision,
            "reasons": list(self.reasons),
            "violated_rules": list(self.violated_rules),
            "input_sha256": self.input_sha256,
            "engine": dict(self.engine),
            "receipt_status": self.receipt_status,
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        if indent is None:
            return canonical_json(self.payload()).decode("utf-8")
        return json.dumps(
            self.payload(), indent=indent, sort_keys=True, ensure_ascii=False
        )

    @staticmethod
    def parse(payload: Dict[str, Any]) -> "Decision":
        """Fail-closed parse of a decision payload back into a Decision."""
        if not isinstance(payload, dict):
            raise ValueError("decision payload must be a JSON object")
        if payload.get("schema") != DECISION_SCHEMA:
            raise ValueError(f"schema must be {DECISION_SCHEMA}")
        decision = payload.get("decision")
        if decision not in DECISIONS:
            raise ValueError(f"decision must be one of {DECISIONS}")
        reasons = payload.get("reasons")
        violated = payload.get("violated_rules")
        if not isinstance(reasons, list) or not all(
            isinstance(r, str) for r in reasons
        ):
            raise ValueError("reasons must be a list of strings")
        if not isinstance(violated, list) or not all(
            isinstance(v, str) and _RULE_ID_RE.match(v) for v in violated
        ):
            raise ValueError("violated_rules must be doctrine rule ids")
        digest = payload.get("input_sha256")
        if not isinstance(digest, str) or not re.fullmatch(
            r"sha256:[0-9a-f]{64}", digest
        ):
            raise ValueError("input_sha256 must be a sha256 digest")
        if decision == ALLOW and violated:
            raise ValueError("ALLOW with violated rules is incoherent")
        if decision == BLOCK and not violated and not reasons:
            raise ValueError("BLOCK must carry reasons")
        return Decision(
            decision=decision,
            reasons=list(reasons),
            violated_rules=list(violated),
            input_sha256=digest,
            rule_version=payload.get("rule_version", RULE_VERSION),
            engine=dict(payload.get("engine") or {}),
            receipt_status=payload.get("receipt_status", UNSIGNED_HONEST),
        )


__all__ = [
    "ALLOW",
    "BLOCK",
    "REVIEW",
    "DECISIONS",
    "DECISION_SCHEMA",
    "RECEIPT_SCHEMA",
    "RULE_VERSION",
    "UNSIGNED_HONEST",
    "Decision",
    "RuleCheckInput",
    "canonical_json",
    "sha256_hex",
]
