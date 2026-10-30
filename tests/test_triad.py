# SPDX-License-Identifier: Apache-2.0
"""Triad binder: proposal, joules or null, and a non-authorizing Λ score."""
from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from szl_nemo.cli import main
from szl_nemo.triad import (
    LAMBDA_STATUS_LABEL,
    evaluate_triad,
    geometric_mean,
    strict_json_loads,
)

HEX = "ab" * 32
OTHER = "cd" * 32


def _document() -> dict:
    return {
        "authorization": {
            "principal_id_sha256": HEX,
            "tenant_id_sha256": OTHER,
            "access_decision": "ALLOW",
            "policy_revision": "sha256:" + ("e" * 64),
            "request_sha256": "f" * 64,
        },
        "proposal": {
            "family": "NVIDIA_NEMOTRON",
            "authority": "PROPOSAL_ONLY",
            "output_sha256": "1" * 64,
            "model_id": "nvidia/nemotron-example",
            "model_revision": "a" * 40,
        },
        "energy": {"joules": None, "label": "UNAVAILABLE", "source": "NVML_ABSENT"},
        "lambda": {"scores": [1.0, 0.25]},
    }


class TriadTests(unittest.TestCase):
    def test_geometric_mean_zero_axis_is_zero(self) -> None:
        self.assertEqual(geometric_mean([0.0, 1.0]), 0.0)

    def test_geometric_mean_equal_weights(self) -> None:
        self.assertTrue(math.isclose(geometric_mean([1.0, 0.25]), 0.5))

    def test_allow_null_energy_is_unsigned_and_not_nemotron(self) -> None:
        decision = evaluate_triad(_document())
        record = decision.record()
        self.assertEqual(decision.decision, "ALLOW")
        self.assertEqual(decision.reasons, ())
        self.assertTrue(math.isclose(record["lambda"]["score"], 0.5))
        self.assertEqual(record["lambda"]["score_label"], "MODELED")
        self.assertEqual(record["lambda"]["can_authorize"], False)
        self.assertEqual(record["lambda"]["status_label"], LAMBDA_STATUS_LABEL)
        self.assertEqual(record["lambda"]["unconditional_uniqueness"], "FALSE_AS_STATED")
        self.assertIsNone(record["energy"]["joules"])
        self.assertEqual(record["energy"]["label"], "UNAVAILABLE")
        self.assertEqual(record["proposal"]["authority"], "PROPOSAL_ONLY")
        self.assertTrue(record["witness_identity"]["not_nemotron"])
        self.assertIsNone(record["dsse"])
        self.assertEqual(record["receipt_status"], "UNSIGNED_HONEST")
        self.assertEqual(record["darpa"]["szl_award"], "NONE_ASSERTED")
        self.assertEqual(record["nvidia"]["role"], "PROPOSAL_ONLY")
        again = evaluate_triad(_document())
        self.assertEqual(decision.body_json, again.body_json)

    def test_measured_joules_pass(self) -> None:
        document = _document()
        document["energy"] = {"joules": 2, "label": "MEASURED", "source": "NVML"}
        record = evaluate_triad(document).record()
        self.assertEqual(record["decision"], "ALLOW")
        self.assertEqual(record["energy"]["joules"], 2.0)
        self.assertEqual(record["energy"]["label"], "MEASURED")

    def test_measured_null_blocks(self) -> None:
        document = _document()
        document["energy"] = {"joules": None, "label": "MEASURED", "source": "NVML"}
        decision = evaluate_triad(document)
        self.assertEqual(decision.decision, "BLOCK")
        self.assertIn(
            "MEASURED energy needs a finite non-negative joule value",
            decision.reasons,
        )

    def test_unavailable_with_a_number_blocks(self) -> None:
        document = _document()
        document["energy"] = {"joules": 1.0, "label": "UNAVAILABLE", "source": "NVML_ABSENT"}
        self.assertEqual(evaluate_triad(document).decision, "BLOCK")

    def test_non_finite_joules_block(self) -> None:
        document = _document()
        document["energy"] = {
            "joules": float("inf"),
            "label": "MEASURED",
            "source": "NVML",
        }
        self.assertEqual(evaluate_triad(document).decision, "BLOCK")

    def test_execution_authority_blocks(self) -> None:
        document = _document()
        document["proposal"]["authority"] = "EXECUTE"
        decision = evaluate_triad(document)
        self.assertEqual(decision.decision, "BLOCK")
        self.assertIn("model authority is not PROPOSAL_ONLY", decision.reasons)

    def test_signature_field_blocks(self) -> None:
        document = _document()
        document["dsse"] = {"signature": "not-checked"}
        self.assertEqual(evaluate_triad(document).decision, "BLOCK")

    def test_proven_flag_blocks(self) -> None:
        document = _document()
        document["lambda"]["proven"] = True
        self.assertEqual(evaluate_triad(document).decision, "BLOCK")

    def test_bool_score_blocks(self) -> None:
        document = _document()
        document["lambda"]["scores"] = [True, 1.0]
        self.assertEqual(evaluate_triad(document).decision, "BLOCK")

    def test_unauthorized_caller_blocks(self) -> None:
        document = _document()
        document["authorization"]["access_decision"] = "DENY"
        self.assertIn("caller is not authorized", evaluate_triad(document).reasons)

    def test_strict_json_rejects_overflow_and_duplicates(self) -> None:
        with self.assertRaises(ValueError):
            strict_json_loads('{"joules":1e999}')
        with self.assertRaises(ValueError):
            strict_json_loads('{"joules":1,"joules":2}')

    def test_cli_allow_and_overflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "triad.json"
            path.write_text(json.dumps(_document()), encoding="utf-8")
            self.assertEqual(main(["triad-check", str(path)]), 0)
            path.write_text('{"energy":{"joules":1e999}}', encoding="utf-8")
            self.assertEqual(main(["triad-check", str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
