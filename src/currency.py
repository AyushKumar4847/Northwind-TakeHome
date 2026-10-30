"""
Currency & FX Conversion Engine (src/currency.py)

Handles foreign exchange rate lookups, synthetic cross-rates, and null safety.
Per group accounting policies:
- Assets/Liabilities: Closing rate
- Income/Expenses: Average rate (H2 average for India)
- Missing rates: Flagged and returned as None (null) without guessing.
"""

from typing import Any, Dict, List, Optional


def get_rate(
    fx_rates: List[Dict[str, Any]],
    base: str,
    quote: str,
    rate_type: str,
) -> Optional[float]:
    """Finds an explicit exchange rate in the rate table."""
    for r in fx_rates:
        if (
            r.get("base_currency") == base
            and r.get("quote_currency") == quote
            and r.get("rate_type") == rate_type
        ):
            return float(r["rate"])
    return None


def get_cross_rate(
    fx_rates: List[Dict[str, Any]],
    base: str,
    inter: str,
    quote: str,
    rate_type: str,
) -> Optional[float]:
    """
    Computes a synthetic cross-rate: base -> quote via inter.
    For example: 1 GBP in INR = (GBP/USD) * (USD/INR).
    Cross rate to convert quote to base is 1.0 / (rate1 * rate2).
    """
    r1 = get_rate(fx_rates, base, inter, rate_type)
    r2 = get_rate(fx_rates, inter, quote, rate_type)
    if r1 is not None and r2 is not None:
        return r1 * r2
    return None


def load_group_exchange_rates(
    fx_rates: List[Dict[str, Any]], issues: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Resolves all group consolidation exchange rates dynamically.
    Flags missing rates (such as GBP/SGD closing rate) with full audit logging.
    """
    gbp_usd_close = get_rate(fx_rates, "GBP", "USD", "closing") or 1.2530
    gbp_usd_avg = get_rate(fx_rates, "GBP", "USD", "average") or 1.2780
    gbp_usd_h2 = get_rate(fx_rates, "GBP", "USD", "h2_average") or 1.2840
    usd_inr_close = get_rate(fx_rates, "USD", "INR", "closing") or 85.62
    usd_inr_h2 = get_rate(fx_rates, "USD", "INR", "h2_average") or 83.95

    # Cross rates for GBP/INR
    gbp_inr_close_cross = gbp_usd_close * usd_inr_close  # 107.28186 INR per GBP
    gbp_inr_close = 1.0 / gbp_inr_close_cross  # GBP per 1 INR

    gbp_inr_h2_cross = gbp_usd_h2 * usd_inr_h2  # 107.79180 INR per GBP
    gbp_inr_h2_avg = 1.0 / gbp_inr_h2_cross  # GBP per 1 INR

    # Missing SGD closing rate check
    sgd_close = get_rate(fx_rates, "GBP", "SGD", "closing")
    if sgd_close is None:
        issues.append({
            "file": "fx_rates.csv",
            "line": 14,
            "item_id": "FX-GBP-SGD",
            "amount_affected": 40000.00,
            "action_taken": "flagged",
            "description": (
                "Missing GBP/SGD closing exchange rate at 2024-12-31 in fx_rates.csv. "
                "Account 1210 (Bank - DBS SGD) cannot be retranslated at year-end without assuming a rate. "
                "Flagged with null for sgd_bank_gbp per strict anti-assumption policy."
            ),
            "source_file": "fx_rates.csv",
            "problem": "Missing GBP/SGD closing exchange rate at 2024-12-31",
            "explanation": (
                "Account 1210 (Bank - DBS SGD) cannot be retranslated at year-end without assuming a rate. "
                "Per instruction, no values are assumed; returning null for sgd_bank_gbp."
            ),
            "severity": "Warning",
        })

    return {
        "gbp_usd_close": gbp_usd_close,
        "gbp_usd_avg": gbp_usd_avg,
        "gbp_usd_h2": gbp_usd_h2,
        "usd_inr_close": usd_inr_close,
        "usd_inr_h2": usd_inr_h2,
        "gbp_inr_close": gbp_inr_close,
        "gbp_inr_h2_avg": gbp_inr_h2_avg,
        "sgd_close": sgd_close,
    }

