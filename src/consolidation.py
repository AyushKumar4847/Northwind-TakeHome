"""
Consolidation Engine (src/consolidation.py)

Performs multi-currency ledger aggregation across subsidiaries:
1. Double-entry net debit/credit balance arithmetic.
2. Applies posted adjustments to local ledgers (US, UK, India).
3. Translates foreign subsidiary accounts into presentation currency (GBP).
4. Assembles group trial balance figures.
"""

from typing import Any, Dict, List, Tuple


def net_dr(d: Dict[str, Dict[str, float]], code: str) -> float:
    """Returns net debit balance (Debit - Credit) for Assets and Expenses."""
    acc = d.get(code, {"debit": 0.0, "credit": 0.0})
    return acc["debit"] - acc["credit"]


def net_cr(d: Dict[str, Dict[str, float]], code: str) -> float:
    """Returns net credit balance (Credit - Debit) for Liabilities, Equity, and Revenue."""
    acc = d.get(code, {"debit": 0.0, "credit": 0.0})
    return acc["credit"] - acc["debit"]


def aggregate_entity_accounts(
    data: Dict[str, Any],
    posted_journals: List[Dict[str, Any]],
    clean_map_uk: Dict[str, str],
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]], Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
    """
    Aggregates ledger accounts across US, UK, and India, incorporating posted journal adjustments.
    Returns:
        (us_acc, uk_acc, in_acc_bs, in_pl_h2)
    """
    # 1. Aggregate US Trial Balance (NetSuite) + US posted adjustments
    us_acc: Dict[str, Dict[str, float]] = {
        r["account_code"]: {"debit": r["debit"], "credit": r["credit"]}
        for r in data["tb_us"]
    }
    for j in posted_journals:
        if j.get("entity") == "US":
            for l in j.get("lines", []):
                code = l["account"]
                if code not in us_acc:
                    us_acc[code] = {"debit": 0.0, "credit": 0.0}
                us_acc[code]["debit"] += l["debit"]
                us_acc[code]["credit"] += l["credit"]

    # 2. Aggregate UK Trial Balance (Sage 50) + UK posted adjustments (mapped to group codes)
    uk_acc: Dict[str, Dict[str, float]] = {}
    for r in data["tb_uk"]:
        gcode = clean_map_uk.get(r["nominal_code"])
        if not gcode:
            continue
        if gcode not in uk_acc:
            uk_acc[gcode] = {"debit": 0.0, "credit": 0.0}
        b = r["balance"]
        if b >= 0:
            uk_acc[gcode]["debit"] += b
        else:
            uk_acc[gcode]["credit"] += abs(b)
    for j in posted_journals:
        if j.get("entity") == "UK":
            for l in j.get("lines", []):
                gcode = clean_map_uk.get(l["account"])
                if gcode:
                    if gcode not in uk_acc:
                        uk_acc[gcode] = {"debit": 0.0, "credit": 0.0}
                    uk_acc[gcode]["debit"] += l["debit"]
                    uk_acc[gcode]["credit"] += l["credit"]

    # 3. Aggregate India Balance Sheet (Tally Prime) + India posted adjustments
    in_acc: Dict[str, Dict[str, float]] = {}
    for r in data["tb_in"]:
        gcode = data["map_in"].get(r["ledger_code"])
        if not gcode:
            continue
        if gcode not in in_acc:
            in_acc[gcode] = {"debit": 0.0, "credit": 0.0}
        amt = r["amount"]
        if r["dr_cr"] == "Dr":
            in_acc[gcode]["debit"] += amt
        else:
            in_acc[gcode]["credit"] += amt
    for j in posted_journals:
        if j.get("entity") == "IN":
            for l in j.get("lines", []):
                gcode = data["map_in"].get(l["account"])
                if gcode:
                    if gcode not in in_acc:
                        in_acc[gcode] = {"debit": 0.0, "credit": 0.0}
                    in_acc[gcode]["debit"] += l["debit"]
                    in_acc[gcode]["credit"] += l["credit"]

    # 4. Aggregate India Post-Acquisition (H2) P&L + India posted adjustments
    months_h2 = ["2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"]
    in_pl: Dict[str, Dict[str, float]] = {}
    for r in data["in_pl_monthly"]:
        if r["month"] in months_h2:
            gcode = data["map_in"].get(r["ledger_code"])
            if not gcode:
                continue
            if gcode not in in_pl:
                in_pl[gcode] = {"debit": 0.0, "credit": 0.0}
            if r["dr_cr"] == "Dr":
                in_pl[gcode]["debit"] += r["amount"]
            else:
                in_pl[gcode]["credit"] += r["amount"]
    for j in posted_journals:
        if j.get("entity") == "IN":
            for l in j.get("lines", []):
                gcode = data["map_in"].get(l["account"])
                if gcode and gcode in ["4100", "5100", "6100", "6200", "6400", "6500", "7100", "8100"]:
                    if gcode not in in_pl:
                        in_pl[gcode] = {"debit": 0.0, "credit": 0.0}
                    in_pl[gcode]["debit"] += l["debit"]
                    in_pl[gcode]["credit"] += l["credit"]

    return us_acc, uk_acc, in_acc, in_pl

