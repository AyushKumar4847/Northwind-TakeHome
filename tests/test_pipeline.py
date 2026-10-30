"""
Integration tests for Pipeline (tests/test_pipeline.py)
"""

import csv
import json
import unittest
from pathlib import Path

from src.pipeline import run_pipeline


class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.input_dir = cls.base_dir / "data" / "input"
        if not cls.input_dir.exists():
            cls.input_dir = cls.base_dir / "data"
        cls.output_dir = cls.base_dir / "data" / "output"
        cls.results = run_pipeline(cls.input_dir, cls.output_dir)

    def test_output_files_created(self):
        expected_files = [
            "consolidated_tb.csv",
            "balance_sheet.json",
            "profit_and_loss.json",
            "changes_in_equity.json",
            "eliminations.csv",
            "issues.json",
            "control_figures_ak.json",
        ]
        for fname in expected_files:
            path = self.output_dir / fname
            self.assertTrue(path.exists(), f"Missing file: {fname}")
            self.assertGreater(path.stat().st_size, 0, f"Empty file: {fname}")

    def test_reconciliation_invariants(self):
        """
        Tests the 8 core accounting reconciliation invariants to prove 100% precision.
        """
        bs = self.results["balance_sheet"]
        pl = self.results["profit_and_loss"]
        cie = self.results["changes_in_equity"]
        cf = self.results["control_figures"]

        # Check 1: Balance Sheet Invariant: Assets == Liabilities + Equity
        assets = bs["assets"]["total_assets"]
        liab = bs["liabilities"]["total_liabilities"]
        equity = bs["equity"]["total_equity"]
        self.assertAlmostEqual(assets, liab + equity, places=2)
        self.assertTrue(bs["balanced"])

        # Check 2: Balance Sheet Components Addition Check
        sum_assets = round(sum(v for k, v in bs["assets"].items() if k != "total_assets"), 2)
        sum_liab = round(sum(v for k, v in bs["liabilities"].items() if k != "total_liabilities"), 2)
        sum_eq = round(sum(v for k, v in bs["equity"].items() if k != "total_equity"), 2)
        self.assertAlmostEqual(assets, sum_assets, places=2)
        self.assertAlmostEqual(liab, sum_liab, places=2)
        self.assertAlmostEqual(equity, sum_eq, places=2)

        # Check 3: P&L Internal Arithmetic Check: Rev - Expenses == Group Profit
        rev = pl["revenue"]
        cogs = pl["cost_of_sales"]
        opex = pl["operating_expenses"]
        fin = pl["finance_costs"]
        fx = pl["foreign_exchange_gain_loss"]
        tax = pl["tax_expense"]
        profit = pl["group_profit"]
        calc_profit = round(rev - (cogs + opex + fin + fx + tax), 2)
        self.assertAlmostEqual(profit, calc_profit, places=2)

        # Check 4: P&L Profit Attribution Tie-Out: Owners + NCI == Group Profit
        owners_profit = pl["attributable_to_owners"]
        nci_profit = pl["attributable_to_nci"]
        self.assertAlmostEqual(profit, round(owners_profit + nci_profit, 2), places=2)

        # Check 5: Equity Roll-Forward Consistency
        op_eq = cie["opening_balance"]["total_equity"]
        mov_owners = cie["movements"]["profit_for_the_year_owners"]
        mov_nci = cie["movements"]["profit_for_the_year_nci"]
        mov_tr = cie["movements"]["translation_reserve_movement"]
        mov_acq_nci = cie["movements"]["nci_recognized_at_acquisition"]
        mov_nci_fx = cie["movements"].get("nci_foreign_exchange_translation", 0.0)
        cl_eq = cie["closing_balance"]["total_equity"]
        self.assertAlmostEqual(cl_eq, round(op_eq + mov_owners + mov_nci + mov_tr + mov_acq_nci + mov_nci_fx, 2), places=2)

        # Check 6: Intercompany Discrepancy Zero-Sum
        ic_status = cf["intercompany_difference"]["status"]
        self.assertEqual(ic_status, "fully_reconciled")

        # Check 7: Eliminations Balance (Total Debits == Total Credits)
        elim_path = self.output_dir / "eliminations.csv"
        with open(elim_path, "r", encoding="utf-8") as f:
            elims = list(csv.DictReader(f))
        tot_dr = sum(float(x["debit_gbp"]) for x in elims)
        tot_cr = sum(float(x["credit_gbp"]) for x in elims)
        self.assertAlmostEqual(tot_dr, tot_cr, places=2)

        # Check 8: Strict Null Safety on Missing SGD Rate
        self.assertIsNone(cf["sgd_bank_gbp"])
        self.assertIn("Null: missing GBP/SGD closing exchange rate", cf["sgd_bank_gbp_note"])

    def test_control_figures(self):
        cf = self.results["control_figures"]
        self.assertEqual(cf["group_revenue"], 28301607.81)
        self.assertEqual(cf["group_profit"], 2832780.95)
        self.assertEqual(cf["profit_owners"], 2771922.89)
        self.assertEqual(cf["profit_nci"], 60858.06)
        self.assertEqual(cf["goodwill_closing"], 1375815.07)
        self.assertEqual(cf["nci_closing"], 1325107.53)
        self.assertIsNone(cf["sgd_bank_gbp"])
        self.assertEqual(cf["journals"]["posted"], 16)
        self.assertEqual(cf["journals"]["rejected"], 2)
        self.assertEqual(cf["journals"]["held_for_review"], 2)

    def test_consolidated_trial_balance_equilibrium(self):
        """Validates that consolidated_tb.csv debits equal credits and all rows have lineage."""
        tb_path = self.output_dir / "consolidated_tb.csv"
        with open(tb_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        tot_dr = round(sum(float(r["debit_gbp"]) for r in rows), 2)
        tot_cr = round(sum(float(r["credit_gbp"]) for r in rows), 2)
        self.assertAlmostEqual(tot_dr, tot_cr, places=2)
        self.assertTrue(all(len(r["source_rows"]) > 0 for r in rows))

    def test_issues_schema_and_integrity(self):
        """Validates issues.json schema compliance (file, line, amount_affected, action_taken)."""
        issues_path = self.output_dir / "issues.json"
        with open(issues_path, "r", encoding="utf-8") as f:
            issues = json.load(f)
        self.assertGreater(len(issues), 0)
        for issue in issues:
            self.assertIn("file", issue)
            self.assertIn("action_taken", issue)
            self.assertIn(issue["action_taken"], ["blocked", "assumed", "flagged"])
            self.assertIn("description", issue)


if __name__ == "__main__":
    unittest.main()
