# SPDX-License-Identifier: Apache-2.0
"""Vector-driven tests: every labelled vector must match ground truth.

Vectors ship as package data in szl_nemo/vectors/*.jsonl, with
expectations COMPUTED by
scripts/build_vectors.py (which refuses to write a mislabelled vector).
These tests make CI enforce them.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from szl_nemo import rule_check  # noqa: E402
from szl_nemo.engine import evaluate  # noqa: E402
from szl_nemo.schema import ALLOW, BLOCK  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Canonical location is the shipped package data so installed-mode
# `szl-nemo selftest` and CI see identical bytes.
VECTORS = os.path.join(ROOT, "szl_nemo", "vectors")


def _load(name):
    path = os.path.join(VECTORS, name)
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_vector_files_exist_and_are_nonempty():
    assert len(_load("allow.jsonl")) >= 8
    assert len(_load("deny.jsonl")) >= 10


def test_allow_vectors_all_conform():
    for record in _load("allow.jsonl"):
        ok, violated = rule_check(record["prompt"], record["answer"])
        assert record["expect"]["ok"] is True, record["id"]
        assert ok is True, f"{record['id']}: {violated}"
        decision = evaluate(record["prompt"], record["answer"])
        assert decision.decision == ALLOW, record["id"]


def test_deny_vectors_all_block_with_exact_rules():
    for record in _load("deny.jsonl"):
        ok, violated = rule_check(record["prompt"], record["answer"])
        assert record["expect"]["ok"] is False, record["id"]
        assert ok is False, record["id"]
        assert violated == record["expect"]["violated"], (
            f"{record['id']}: expected {record['expect']['violated']} got {violated}"
        )
        decision = evaluate(record["prompt"], record["answer"])
        assert decision.decision == BLOCK, record["id"]
        assert list(decision.violated_rules) == record["expect"]["violated"]


def test_vector_ids_are_unique():
    ids = [r["id"] for name in ("allow.jsonl", "deny.jsonl") for r in _load(name)]
    assert len(ids) == len(set(ids))


def test_every_rule_is_covered_by_at_least_one_deny_vector():
    from szl_nemo import RULE_IDS

    covered = set()
    for record in _load("deny.jsonl"):
        covered.update(record["expect"]["violated"])
    assert covered == set(RULE_IDS)
