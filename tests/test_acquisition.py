"""
Unit tests for Module: Acquisition (tests/test_acquisition.py)
"""

import unittest
from pathlib import Path
from src.loader import load_all_data
from src.acquisition import calculate_acquisition_and_goodwill


class TestAcquisition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.input_dir = cls.base_dir / "data" / "input"
        if not cls.input_dir.exists():
            cls.input_dir = cls.base_dir / "data"
        cls.data = load_all_data(cls.input_dir)

    def test_goodwill_and_nci(self):
        # India posted adjustments (JE-012, 013, 018, 020)
        posted = [{"id": f"JE-{i:03d}", "entity": "IN"} for i in [12, 13, 18, 20]]
        res, elims = calculate_acquisition_and_goodwill(self.data, posted)

        self.assertEqual(res["goodwill_closing_gbp"], 1375815.07)
        self.assertEqual(res["nci_closing_gbp"], 1325107.53)
        self.assertEqual(res["profit_nci_gbp"], 60858.06)

        # Check investment elimination double entry (Debits == Credits)
        tot_dr = sum(e["debit"] for e in elims)
        tot_cr = sum(e["credit"] for e in elims)
        self.assertAlmostEqual(tot_dr, tot_cr, places=2)


if __name__ == "__main__":
    unittest.main()

