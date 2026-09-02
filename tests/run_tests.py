#!/usr/bin/env python3
"""Discover and run the categorized Jasp-to-QIR test suite."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import support


if __name__ == "__main__":
    support.start_session()
    result = None
    try:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.discover("tests")
        )
    finally:
        support.finish_session(result is not None and result.wasSuccessful())
    raise SystemExit(not result.wasSuccessful())
