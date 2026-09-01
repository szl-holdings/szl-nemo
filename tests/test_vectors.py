# SPDX-License-Identifier: Apache-2.0
"""Run the repo's allow/deny vectors through the engine, fail closed."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from szl_nemo import ALLOW, BLOCK, evaluate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DIR = os.path.join(ROOT, "test_vectors")


def _load(name):
    path = os.path.join(VECTOR_DIR, name)
    assert os.path.isfile(path), f"missing vector file: {path}"
    rows = []
    with open(path, encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                row["_where"] = f"{name}:{lineno}"
                rows.append(row)
    assert rows, f"{name} must not be empty"
    return rows


def test_allow_vectors_all_conform():
    for row in _load("allow.jsonl"):
        decision = evaluate(row["prompt"], row["answer"])
        assert decision.decision == ALLOW, (row["_where"], decision.reasons)
        assert decision.violated_rules == [], row["_where"]


def test_deny_vectors_all_block_with_expected_rules():
    for row in _load("deny.jsonl"):
        decision = evaluate(row["prompt"], row["answer"])
        assert decision.decision == BLOCK, (row["_where"], decision.reasons)
        expected = row.get("expect_violations")
        assert expected, f"{row['_where']}: deny vectors must declare expect_violations"
        assert sorted(decision.violated_rules) == sorted(expected), (
            row["_where"],
            decision.violated_rules,
            expected,
        )


def test_every_doctrine_rule_has_a_deny_vector():
    covered = set()
    for row in _load("deny.jsonl"):
        covered.update(row.get("expect_violations", []))
    from szl_nemo import RULE_IDS

    missing = set(RULE_IDS) - covered
    assert not missing, f"rules without deny-vector coverage: {sorted(missing)}"
