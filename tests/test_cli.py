# SPDX-License-Identifier: Apache-2.0
"""CLI smoke: exit codes are the contract (0 ALLOW, 1 BLOCK, 2 REVIEW)."""
from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "szl_nemo", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
        timeout=60,
    )


def test_check_allow_exit_0():
    result = _run(
        "check",
        "--prompt", "How good is SZL-Nemo?",
        "--answer", "Quality is UNKNOWN until measured on SZL hardware.",
    )
    assert result.returncode == 0, result.stderr
    assert "decision: ALLOW" in result.stdout


def test_check_block_exit_1_with_json():
    result = _run(
        "check",
        "--prompt", "What's your MMLU?",
        "--answer", "I aim for honesty; my MMLU is 73.",
        "--json",
    )
    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    assert payload["decision"] == "BLOCK"
    assert "R1_no_fabrication_label" in payload["violated_rules"]


def test_check_review_exit_2():
    result = _run("check", "--prompt", "", "--answer", "anything")
    assert result.returncode == 2, result.stderr
    assert "decision: REVIEW" in result.stdout


def test_vectors_pass():
    result = _run("vectors", "--dir", "test_vectors")
    assert result.returncode == 0, result.stderr + result.stdout
    assert "vectors conform" in result.stdout


def test_receipt_verify_roundtrip(tmp_path):
    decision = _run(
        "check",
        "--prompt", "What is szl-nemo?",
        "--answer", "A deterministic doctrine rule_check package.",
        "--json",
        "--receipt",
    )
    assert decision.returncode == 0, decision.stderr
    # stdout is the decision JSON followed by the receipt JSON.
    decoder = json.JSONDecoder()
    _, offset = decoder.raw_decode(decision.stdout)
    receipt, _ = decoder.raw_decode(decision.stdout[offset:].lstrip())
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")

    ok = _run("receipt-verify", str(path))
    assert ok.returncode == 0, ok.stderr + ok.stdout

    receipt["decision"]["decision"] = "BLOCK"
    bad_path = tmp_path / "tampered.json"
    bad_path.write_text(json.dumps(receipt), encoding="utf-8")
    bad = _run("receipt-verify", str(bad_path))
    assert bad.returncode == 1
    assert "FAIL" in bad.stdout
