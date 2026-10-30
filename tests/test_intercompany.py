"""
Unit tests for Module: Intercompany (tests/test_intercompany.py)
"""

import unittest
from pathlib import Path
from src.loader import load_all_data
from src.intercompany import reconcile_intercompany


class TestIntercompany(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.input_dir = cls.base_dir / "data" / "input"
        if not cls.input_dir.exists():
            cls.input_dir = cls.base_dir / "data"
        cls.data = load_all_data(cls.input_dir)

    def test_intercompany_reconciliation(self):
        issues = []
        details, elims = reconcile_intercompany(self.data, self.data["fx_rates"], issues)
        summary = details["summary"]

        self.assertEqual(summary["status"], "fully_reconciled")
        self.assertAlmostEqual(summary["total_difference_unadjusted_gbp"], 20066.42, places=2)
        self.assertAlmostEqual(summary["causes"]["in_transit_invoice_INV-US-2291_gbp"], 8108.54, places=2)
        self.assertAlmostEqual(summary["causes"]["unrealized_fx_revaluation_of_uk_liability_gbp"], 11957.88, places=2)

        # Check elimination debits == credits
        tot_dr = sum(e["debit"] for e in elims)
        tot_cr = sum(e["credit"] for e in elims)
        self.assertAlmostEqual(tot_dr, tot_cr, places=2)


if __name__ == "__main__":
    unittest.main()

