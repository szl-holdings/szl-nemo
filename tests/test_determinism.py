# SPDX-License-Identifier: Apache-2.0
"""Determinism: same input must produce byte-identical decisions,
across repeated calls and across separate processes."""
from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from szl_nemo.engine import evaluate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAIR = (
    "Did SZL fine-tune you? What is your MMLU?",
    "SZL did not fine-tune these weights. MMLU is UNKNOWN - not yet measured.",
)


def test_repeated_evaluation_is_byte_identical():
    runs = [evaluate(*PAIR).to_json() for _ in range(5)]
    assert len(set(runs)) == 1


def test_unicode_input_is_byte_identical():
    runs = [evaluate("Explain Λ.", "Λ is Conjecture 1 - open, status UNKNOWN.").to_json() for _ in range(5)]
    assert len(set(runs)) == 1


def test_separate_processes_agree():
    outputs = []
    for _ in range(2):
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "szl_nemo",
                "check",
                "--prompt",
                PAIR[0],
                "--answer",
                PAIR[1],
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        outputs.append(proc.stdout)
    assert outputs[0] == outputs[1]
