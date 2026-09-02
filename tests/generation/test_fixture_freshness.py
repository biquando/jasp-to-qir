import unittest

from tests import support


class FixtureFreshnessTest(unittest.TestCase):
    def test_checked_in_fixtures_are_current(self) -> None:
        support.verify_qrisp_fixtures(support.temp_dir())
