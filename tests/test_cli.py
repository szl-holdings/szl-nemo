# SPDX-License-Identifier: Apache-2.0
"""CLI smoke tests: exit codes, JSON output, batch mode, selftest."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = dict(os.environ, PYTHONPATH=ROOT)


def _run(*argv):
    return subprocess.run(
        [sys.executable, "-m", "szl_nemo", *argv],
        cwd=ROOT,
        env=ENV,
        capture_output=True,
        text=True,
    )


def test_check_allow_exit_0():
    proc = _run(
        "check",
        "--prompt", "What's your MMLU?",
        "--answer", "UNKNOWN - no benchmarks have been run.",
    )
    assert proc.returncode == 0, proc.stderr
    decision = json.loads(proc.stdout)
    assert decision["decision"] == "ALLOW"
    assert decision["input_hash"].startswith("sha256:")


def test_check_block_exit_1():
    proc = _run(
        "check",
        "--prompt", "What's your MMLU?",
        "--answer", "My MMLU is 73.",
    )
    assert proc.returncode == 1
    decision = json.loads(proc.stdout)
    assert decision["decision"] == "BLOCK"
    assert "R1_no_fabrication_label" in decision["violated_rules"]


def test_check_review_exit_3():
    proc = _run("check", "--prompt", "", "--answer", "")
    assert proc.returncode == 3
    decision = json.loads(proc.stdout)
    assert decision["decision"] == "REVIEW"


def test_check_usage_error_exit_2():
    proc = _run("check")
    assert proc.returncode == 2


def test_check_jsonl_batch():
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "pairs.jsonl")
        out = os.path.join(tmp, "decisions.jsonl")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "prompt": "What's your MMLU?",
                "answer": "UNKNOWN - not yet measured.",
            }) + "\n")
            fh.write(json.dumps({
                "prompt": "Explain Λ.",
                "answer": "Λ is a proven theorem.",
            }) + "\n")
        proc = _run("check", "--jsonl", src, "--out", out)
        assert proc.returncode == 1, proc.stderr
        with open(out, encoding="utf-8") as fh:
            decisions = [json.loads(line) for line in fh if line.strip()]
        assert [d["decision"] for d in decisions] == ["ALLOW", "BLOCK"]


def test_selftest_passes():
    proc = _run("selftest")
    assert proc.returncode == 0, proc.stderr
    assert "SELFTEST OK" in proc.stdout


def test_version_reports_contract():
    proc = _run("version")
    assert proc.returncode == 0
    info = json.loads(proc.stdout)
    assert info["package"] == "szl-nemo"
    assert "not an LLM" in info["kind"]
