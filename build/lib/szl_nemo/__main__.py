# SPDX-License-Identifier: Apache-2.0
"""Module entry point: python -m szl_nemo ..."""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
