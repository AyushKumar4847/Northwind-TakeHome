"""
Unit tests for Module: Data Loader (tests/test_loader.py)
"""

import unittest
from pathlib import Path
from src.loader import load_all_data, load_csv_rows


class TestLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.input_dir = cls.base_dir / "data" / "input"
        if not cls.input_dir.exists():
            cls.input_dir = cls.base_dir / "data"
        cls.data = load_all_data(cls.input_dir)

    def test_load_all_files(self):
        expected_keys = [
            "entities",
            "group_coa",
            "map_uk",
            "map_in",
            "fx_rates",
            "tb_us",
            "tb_uk",
            "tb_in",
            "in_pl_monthly",
            "intercompany",
            "subledger_controls",
            "prior_year_group",
            "adjustments",
        ]
        for key in expected_keys:
            self.assertIn(key, self.data)
            self.assertGreater(len(self.data[key]), 0, f"Empty dataset for {key}")

    def test_numeric_parsing(self):
        self.assertIsInstance(self.data["tb_us"][0]["debit"], float)
        self.assertIsInstance(self.data["tb_uk"][0]["balance"], float)
        self.assertIsInstance(self.data["tb_in"][0]["amount"], float)
        self.assertIsInstance(self.data["fx_rates"][0]["rate"], float)

    def test_row_provenance(self):
        self.assertEqual(self.data["tb_us"][0]["row_num"], 2)
        self.assertEqual(self.data["tb_uk"][0]["row_num"], 2)


if __name__ == "__main__":
    unittest.main()
