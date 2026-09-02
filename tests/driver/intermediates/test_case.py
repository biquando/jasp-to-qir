from pathlib import Path
import unittest

from tests import support


class IntermediatesTest(unittest.TestCase):
    def test_keep_intermediates_contract(self) -> None:
        support.verify_intermediates(Path(__file__).parent, support.temp_dir())
