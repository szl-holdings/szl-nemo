# SPDX-License-Identifier: Apache-2.0
"""Enable `python -m szl_nemo`."""
from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
