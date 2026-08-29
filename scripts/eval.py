#!/usr/bin/env python3
"""Fail-closed evaluator.

Approved path: szl_nemo.rule_check (stdlib).
model.joblib is executable serialization and is not an approved load path.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALL = re.compile(r"\b(?:joblib\.(?:load|dump)|pickle\.loads?|dill\.load)\s*\(")
APPROVED = ("scripts", "tests", "szl_nemo")


def main() -> int:
    joblib_path = os.path.join(ROOT, "model.joblib")
    if os.path.exists(joblib_path):
        digest = hashlib.sha256(open(joblib_path, "rb").read()).hexdigest()
        print(f"QUARANTINE: model.joblib present sha256={digest} — not an approved load path")
        return 2
    hits = []
    for rel in APPROVED:
        base = os.path.join(ROOT, rel)
        if not os.path.isdir(base):
            continue
        for dirpath, _, files in os.walk(base):
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(dirpath, name)
                text = open(path, encoding="utf-8").read()
                for i, line in enumerate(text.splitlines(), 1):
                    if CALL.search(line):
                        hits.append(f"{path}:{i}:{line.strip()}")
    if hits:
        print("QUARANTINE: forbidden loader calls still in approved path:")
        print("\n".join(hits))
        return 2
    print("PASS: no model.joblib; no pickle loader calls in approved path. rule_check is ground truth.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
