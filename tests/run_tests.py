#!/usr/bin/env python3
"""Standard unittest CLI with isolated caches and a semantic report."""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests import support


def main() -> int:
    os.chdir(ROOT)
    support.start_session()
    success = False
    try:
        args = sys.argv[1:] or ['discover', '-s', 'tests', '-t', '.']
        result = unittest.main(module=None, argv=[sys.argv[0], *args],
                               verbosity=2, exit=False).result
        success = result.wasSuccessful() and result.testsRun > 0
    finally:
        support.finish_session(success)
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
