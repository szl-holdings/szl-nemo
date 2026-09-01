# SPDX-License-Identifier: Apache-2.0
"""Deterministic doctrine decision engine for szl-nemo.

Semantics (fail-closed, stdlib-only, no model weights involved):

- REVIEW  — the input carries no doctrine signal (empty prompt or answer).
            A human must look at it; the checker refuses to silently allow.
- BLOCK   — one or more doctrine rules R1-R5 are violated.
- ALLOW   — rule_check() finds no violation. This is a conformance claim
            over the text, never a quality or truth claim.

rule_check() remains the ground truth; this engine only shapes its result
into the typed decision contract and never weakens it.
"""
from __future__ import annotations

from typing import List

from .rules import rule_check
from .schema import ALLOW, BLOCK, REVIEW, Decision, RuleCheckInput

REASONS = {
    "R1_no_fabrication_label": (
        "numeric/benchmark claim lacks an honesty label "
        "(MEASURED/REPORTED/MODELED/HEURISTIC/UNKNOWN/UNAVAILABLE)"
    ),
    "R2_honest_unknown": (
        "benchmark/quality question answered with an invented number "
        "instead of an honest UNKNOWN"
    ),
    "R3_not_finetuned": (
        "fine-tune provenance question answered without disclosing that "
        "SZL did not fine-tune the weights"
    ),
    "R4_lambda_not_theorem": (
        "Lambda described as proven/theorem/certified — it remains "
        "Conjecture 1 (open)"
    ),
    "R5_trust_ceiling": (
        "claims 100%/perfect/complete trust — the trust ceiling is 0.97"
    ),
}

REVIEW_REASON = (
    "empty prompt or answer carries no doctrine signal; review manually "
    "instead of allowing by default"
)


def evaluate(prompt: str, answer: str) -> Decision:
    """Evaluate one prompt/answer pair against doctrine R1-R5."""
    check_input = RuleCheckInput(prompt=prompt, answer=answer)
    digest = check_input.digest()

    problems = check_input.validate()
    if problems:
        return Decision(
            decision=REVIEW,
            reasons=[REVIEW_REASON] + problems,
            violated_rules=[],
            input_sha256=digest,
        )

    conforms, violated = rule_check(prompt, answer)
    if conforms:
        return Decision(
            decision=ALLOW,
            reasons=["no doctrine rule violated by this answer"],
            violated_rules=[],
            input_sha256=digest,
        )

    reasons: List[str] = [REASONS.get(rule, rule) for rule in violated]
    return Decision(
        decision=BLOCK,
        reasons=reasons,
        violated_rules=list(violated),
        input_sha256=digest,
    )


__all__ = ["REASONS", "REVIEW_REASON", "evaluate"]
