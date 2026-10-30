"""
Northwind Group Financial Consolidation Package (src)
"""

from src.loader import load_all_data
from src.validation import detect_prompt_injection, validate_trial_balances_and_subledgers
from src.mapping import fix_chart_of_accounts_mapping
from src.currency import load_group_exchange_rates, get_rate, get_cross_rate
from src.journals import process_journal_adjustments
from src.intercompany import reconcile_intercompany
from src.acquisition import calculate_acquisition_and_goodwill
from src.consolidation import aggregate_entity_accounts, net_dr, net_cr
from src.statements import export_all_deliverables
from src.pipeline import run_pipeline

__all__ = [
    "load_all_data",
    "detect_prompt_injection",
    "validate_trial_balances_and_subledgers",
    "fix_chart_of_accounts_mapping",
    "load_group_exchange_rates",
    "get_rate",
    "get_cross_rate",
    "process_journal_adjustments",
    "reconcile_intercompany",
    "calculate_acquisition_and_goodwill",
    "aggregate_entity_accounts",
    "net_dr",
    "net_cr",
    "export_all_deliverables",
    "run_pipeline",
]
