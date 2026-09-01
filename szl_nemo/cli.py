# SPDX-License-Identifier: Apache-2.0
"""Command-line interface for the szl-nemo doctrine kernel.

Stdlib only. Exit codes: 0 = every checked pair is ALLOW,
1 = at least one BLOCK, 2 = usage or I/O error.

Examples:
    python -m szl_nemo check --prompt "What's your MMLU?" \\
        --answer "UNKNOWN - no benchmarks run yet."
    python -m szl_nemo check --jsonl pairs.jsonl --out decisions.jsonl
    python -m szl_nemo selftest
    python -m szl_nemo version
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .engine import evaluate
from .schema import ALLOW, RULE_VERSION, SCHEMA_VERSION

EXIT_ALLOW = 0
EXIT_BLOCK = 1
EXIT_ERROR = 2

_VECTORS_DIR = Path(__file__).resolve().parent.parent / "test_vectors"


def _print_decision(decision, out) -> None:
    out.write(decision.to_json() + "\n")


def _cmd_check(args: argparse.Namespace) -> int:
    if args.jsonl:
        path = Path(args.jsonl)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return EXIT_ERROR
        dest = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
        blocked = False
        try:
            for lineno, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                try:
                    pair = json.loads(line)
                    decision = evaluate(pair["prompt"], pair["answer"])
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                    print(f"error: {path}:{lineno}: {exc}", file=sys.stderr)
                    return EXIT_ERROR
                if decision.decision != ALLOW:
                    blocked = True
                _print_decision(decision, dest)
        finally:
            if dest is not sys.stdout:
                dest.close()
        return EXIT_BLOCK if blocked else EXIT_ALLOW

    if args.prompt is None or args.answer is None:
        print("error: check requires --prompt and --answer, or --jsonl", file=sys.stderr)
        return EXIT_ERROR
    decision = evaluate(args.prompt, args.answer)
    _print_decision(decision, sys.stdout)
    return EXIT_ALLOW if decision.decision == ALLOW else EXIT_BLOCK


def _cmd_selftest(_args: argparse.Namespace) -> int:
    """Run the labelled test vectors. This is the kernel's own proof."""
    failures: List[str] = []
    total = 0
    for name in ("allow.jsonl", "deny.jsonl"):
        path = _VECTORS_DIR / name
        if not path.is_file():
            print(f"error: missing vectors file {path}", file=sys.stderr)
            return EXIT_ERROR
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            total += 1
            decision = evaluate(record["prompt"], record["answer"])
            expect = record["expect"]
            actual = (decision.decision == ALLOW, list(decision.violated_rules))
            wanted = (bool(expect["ok"]), list(expect["violated"]))
            if actual != wanted:
                failures.append(
                    f"{name}:{lineno} id={record.get('id')} "
                    f"expected {wanted} got {actual}"
                )
    if failures:
        print("SELFTEST FAIL:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return EXIT_BLOCK
    print(f"SELFTEST OK: {total}/{total} vectors conform ({RULE_VERSION})")
    return EXIT_ALLOW


def _cmd_version(_args: argparse.Namespace) -> int:
    print(
        json.dumps(
            {
                "package": "szl-nemo",
                "version": __version__,
                "schema_version": SCHEMA_VERSION,
                "rule_version": RULE_VERSION,
                "kind": "deterministic doctrine rule_check; not an LLM; not a CUDA kernel",
            },
            indent=2,
        )
    )
    return EXIT_ALLOW


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="szl-nemo",
        description=(
            "Deterministic SZL doctrine kernel (rule_check R1-R5). "
            "Software, not a trained model."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="evaluate prompt/answer pairs")
    check.add_argument("--prompt", default=None)
    check.add_argument("--answer", default=None)
    check.add_argument(
        "--jsonl",
        default=None,
        help="path to JSONL file of {'prompt','answer'} records",
    )
    check.add_argument("--out", default=None, help="write decisions JSONL here")
    check.set_defaults(func=_cmd_check)

    selftest = sub.add_parser("selftest", help="run labelled test vectors")
    selftest.set_defaults(func=_cmd_selftest)

    version = sub.add_parser("version", help="print version and contract info")
    version.set_defaults(func=_cmd_version)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
