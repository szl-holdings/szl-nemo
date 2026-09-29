# SPDX-FileCopyrightText: 2026 SZL Holdings
# SPDX-License-Identifier: Apache-2.0
"""hf/hub-import/ still holds the exact bytes the Hub served when imported.

Offline; no Hub access. See hf/README.md and scripts/hf_hub_import.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _importer():
    spec = importlib.util.spec_from_file_location("hf_hub_import", _ROOT / "scripts" / "hf_hub_import.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hub_import_matches_recorded_digests():
    assert _importer().verify() == []
