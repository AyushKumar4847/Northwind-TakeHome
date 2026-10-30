"""
Unit tests for Module: Journals (tests/test_journals.py)
"""

import unittest
from pathlib import Path
from src.loader import load_all_data
from src.mapping import fix_chart_of_accounts_mapping
from src.journals import process_journal_adjustments


class TestJournals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.input_dir = cls.base_dir / "data" / "input"
        if not cls.input_dir.exists():
            cls.input_dir = cls.base_dir / "data"
        cls.data = load_all_data(cls.input_dir)

    def test_journal_classification(self):
        issues = []
        clean_map = fix_chart_of_accounts_mapping(self.data["map_uk"], issues)
        valid_accounts = {
            "US": list(self.data["group_coa"].keys()),
            "UK": list(clean_map.keys()),
            "IN": list(self.data["map_in"].keys()),
        }
        posted, counts = process_journal_adjustments(
            self.data["adjustments"], valid_accounts, issues
        )
        self.assertEqual(counts["posted"], 16)
        self.assertEqual(counts["rejected"], 2)
        self.assertEqual(counts["held_for_review"], 2)

        # Check blocked IDs
        blocked_ids = [i["item_id"] for i in issues if i["action_taken"] == "blocked"]
        self.assertIn("JE-006", blocked_ids)
        self.assertIn("JE-017", blocked_ids)

        # Check flagged IDs
        flagged_ids = [i["item_id"] for i in issues if i["action_taken"] == "flagged"]
        self.assertIn("JE-016", flagged_ids)
        self.assertIn("JE-019", flagged_ids)


if __name__ == "__main__":
    unittest.main()

