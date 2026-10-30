"""
Unit tests for Module: Mapping (tests/test_mapping.py)
"""

import unittest
from pathlib import Path
from src.loader import load_all_data
from src.mapping import fix_chart_of_accounts_mapping


class TestMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.input_dir = cls.base_dir / "data" / "input"
        if not cls.input_dir.exists():
            cls.input_dir = cls.base_dir / "data"
        cls.data = load_all_data(cls.input_dir)

    def test_fix_uk_mapping(self):
        issues = []
        clean_map = fix_chart_of_accounts_mapping(self.data["map_uk"], issues)
        self.assertEqual(clean_map["2310"], "2300")
        self.assertTrue(any(i["item_id"] == "MAP-UK-2310" for i in issues))


if __name__ == "__main__":
    unittest.main()

