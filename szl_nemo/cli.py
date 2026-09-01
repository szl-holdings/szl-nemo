# SPDX-License-Identifier: Apache-2.0
"""Command-line surface for szl-nemo. Stdlib only, exit codes fail closed.

  python -m szl_nemo check --prompt "..." --answer "..." [--json]
  python -m szl_nemo vectors [--dir test_vectors]
  python -m szl_nemo receipt-verify PATH [PATH ...]

Exit codes: 0 = ALLOW / all vectors pass / all receipts verify.
            1 = BLOCK or verification failure.
            2 = REVIEW or usage/IO error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .engine import evaluate
from .receipt import build_receipt, verify_receipt
from .schema import ALLOW, BLOCK, REVIEW

_DECISION_EXIT = {ALLOW: 0, BLOCK: 1, REVIEW: 2}


def _cmd_check(args: argparse.Namespace) -> int:
    decision = evaluate(prompt=args.prompt, answer=args.answer)
    if args.json:
        print(decision.to_json())
    else:
        print(f"decision: {decision.decision}")
        print(f"rule_version: {decision.rule_version}")
        print(f"input_sha256: {decision.input_sha256}")
        for reason in decision.reasons:
            print(f"reason: {reason}")
        if decision.violated_rules:
            print("violated_rules: " + ", ".join(decision.violated_rules))
        print(f"receipt_status: {decision.receipt_status}")
    if args.receipt:
        receipt = build_receipt(decision)
        print(json.dumps(receipt, indent=2, sort_keys=True))
    return _DECISION_EXIT[decision.decision]


def _load_vectors(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    vectors: List[Dict[str, Any]] = []
    errors: List[str] = []
    if not path.is_file():
        return vectors, [f"missing vector file: {path}"]
    for lineno, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{lineno}: invalid JSON: {exc}")
            continue
        if not isinstance(row.get("prompt"), str) or not isinstance(
            row.get("answer"), str
        ):
            errors.append(f"{path.name}:{lineno}: needs prompt+answer strings")
            continue
        vectors.append(row)
    return vectors, errors


def _cmd_vectors(args: argparse.Namespace) -> int:
    vector_dir = Path(args.dir)
    failures: List[str] = []
    total = 0

    for name, expected in (("allow.jsonl", ALLOW), ("deny.jsonl", BLOCK)):
        vectors, errors = _load_vectors(vector_dir / name)
        failures.extend(errors)
        for row in vectors:
            total += 1
            decision = evaluate(prompt=row["prompt"], answer=row["answer"])
            if decision.decision != expected:
                failures.append(
                    f"{name}: expected {expected}, got {decision.decision} "
                    f"for prompt={row['prompt'][:60]!r}"
                )
                continue
            expect_rules = row.get("expect_violations")
            if expect_rules is not None and sorted(expect_rules) != sorted(
                decision.violated_rules
            ):
                failures.append(
                    f"{name}: expected violations {sorted(expect_rules)}, "
                    f"got {sorted(decision.violated_rules)} "
                    f"for prompt={row['prompt'][:60]!r}"
                )

    if failures:
        print("VECTOR FAILURES:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print(f"OK: {total} vectors conform to the doctrine contract")
    return 0


def _cmd_receipt_verify(args: argparse.Namespace) -> int:
    bad = 0
    for raw in args.paths:
        path = Path(raw)
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL {path}: unreadable or invalid JSON ({exc})")
            bad += 1
            continue
        if verify_receipt(receipt):
            print(
                f"OK {path}: seq={receipt['sequence']} "
                f"{receipt['receipt_sha256'][:23]}… "
                f"({receipt['receipt_status']})"
            )
        else:
            print(f"FAIL {path}: digest, chain, or contract mismatch")
            bad += 1
    return 1 if bad else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="szl-nemo",
        description=(
            "Deterministic SZL doctrine rule_check (R1-R5). SOFTWARE — "
            "not an LLM, not Nemotron, not a CUDA kernel."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="evaluate one prompt/answer pair")
    check.add_argument("--prompt", required=True)
    check.add_argument("--answer", required=True)
    check.add_argument("--json", action="store_true", help="emit decision JSON")
    check.add_argument(
        "--receipt",
        action="store_true",
        help="also emit an UNSIGNED_HONEST hash-chained receipt",
    )
    check.set_defaults(func=_cmd_check)

    vectors = sub.add_parser(
        "vectors", help="run allow/deny test vectors fail-closed"
    )
    vectors.add_argument("--dir", default="test_vectors")
    vectors.set_defaults(func=_cmd_vectors)

    verify = sub.add_parser(
        "receipt-verify", help="verify receipt digests and chain shape"
    )
    verify.add_argument("paths", nargs="+")
    verify.set_defaults(func=_cmd_receipt_verify)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
