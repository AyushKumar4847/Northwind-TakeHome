"""
Unit tests for Module: Currency (tests/test_currency.py)
"""

import unittest
from pathlib import Path
from src.loader import load_all_data
from src.currency import get_rate, get_cross_rate, load_group_exchange_rates


class TestCurrency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.input_dir = cls.base_dir / "data" / "input"
        if not cls.input_dir.exists():
            cls.input_dir = cls.base_dir / "data"
        cls.data = load_all_data(cls.input_dir)

    def test_direct_rates(self):
        r_close = get_rate(self.data["fx_rates"], "GBP", "USD", "closing")
        self.assertEqual(r_close, 1.2530)
        r_avg = get_rate(self.data["fx_rates"], "GBP", "USD", "average")
        self.assertEqual(r_avg, 1.2780)

    def test_cross_rate(self):
        # 1 GBP in INR = (GBP/USD closing) * (USD/INR closing) = 1.2530 * 85.62 = 107.28186
        cross = get_cross_rate(self.data["fx_rates"], "GBP", "USD", "INR", "closing")
        self.assertAlmostEqual(cross, 107.28186, places=5)

    def test_missing_sgd_closing_rate(self):
        issues = []
        fx = load_group_exchange_rates(self.data["fx_rates"], issues)
        self.assertIsNone(fx["sgd_close"])
        self.assertTrue(any("Missing GBP/SGD closing exchange rate" in i.get("problem", "") for i in issues))


if __name__ == "__main__":
    unittest.main()

