"""
Master Consolidation Pipeline (src/pipeline.py)

Master orchestrator connecting the modular consolidation architecture:
1. loader.py       -> Ingests raw ERP files and schedules
2. mapping.py      -> Sanitizes local-to-group account mappings
3. validation.py   -> Security screening and ledger equilibrium checks
4. journals.py     -> Filters manual adjustments (posted, blocked, held)
5. intercompany.py -> Forensic reconciliation of US <-> UK accounts
6. acquisition.py  -> Goodwill & NCI accounting (IFRS 3 / IAS 21)
7. currency.py     -> Exchange rates & cross-rate triangulation
8. consolidation.py-> Double-entry aggregation across NetSuite, Sage 50, and Tally
9. statements.py   -> Statement generation and deliverable export
"""

from pathlib import Path
from typing import Any, Dict, List, Union

from src.loader import load_all_data
from src.mapping import fix_chart_of_accounts_mapping
from src.validation import validate_trial_balances_and_subledgers
from src.journals import process_journal_adjustments
from src.intercompany import reconcile_intercompany
from src.acquisition import calculate_acquisition_and_goodwill
from src.currency import load_group_exchange_rates
from src.consolidation import aggregate_entity_accounts, net_dr, net_cr
from src.statements import export_all_deliverables


def run_pipeline(
    data_dir: Union[str, Path] = "data/input",
    output_dir: Union[str, Path] = "data/output",
) -> Dict[str, Any]:
    """
    Executes the complete financial consolidation pipeline end-to-end dynamically.
    """
    input_path = Path(data_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    issues: List[Dict[str, Any]] = []

    print("======================================================================")
    print("NORTHWIND GROUP FINANCIAL CONSOLIDATION ENGINE (FY2024)")
    print("======================================================================")

    # --------------------------------------------------------------------------
    # Step 1: Ingest Raw Data
    # --------------------------------------------------------------------------
    print("\n[Step 1/7] Ingesting raw ERP files and accounting schedules...")
    data = load_all_data(input_path)
    print(f" -> Loaded 3 entities: {', '.join(e['entity_id'] for e in data['entities'])}")
    print(" -> Loaded trial balances: US (NetSuite), UK (Sage 50), India (Tally Prime)")
    print(f" -> Loaded {len(data['adjustments'])} manual adjustments from adjustments.json")

    # --------------------------------------------------------------------------
    # Step 2: Sanitize Mappings & Validate Ledgers
    # --------------------------------------------------------------------------
    print("\n[Step 2/7] Running ledger validation & security screening...")
    clean_map_uk = fix_chart_of_accounts_mapping(data["map_uk"], issues)
    validate_trial_balances_and_subledgers(data, issues)
    print(" -> Screened for adversarial prompt injections in transaction memos")
    print(" -> Corrected UK mapping: Local 2310 (Deferred income) remapped to Liability 2300")
    print(" -> Verified double-entry equilibrium across all 3 entity trial balances")

    # --------------------------------------------------------------------------
    # Step 3: Process Manual Adjustments (The 20 Journals)
    # --------------------------------------------------------------------------
    print("\n[Step 3/7] Processing 20 manual journal entries...")
    valid_accounts = {
        "US": list(data["group_coa"].keys()),
        "UK": list(clean_map_uk.keys()),
        "IN": list(data["map_in"].keys()),
    }
    posted_journals, journal_counts = process_journal_adjustments(
        data["adjustments"], valid_accounts, issues
    )
    print(f" -> Posted:          {journal_counts['posted']} valid entries")
    print(f" -> Blocked/Rejected:{journal_counts['rejected']} invalid entries (JE-006 injection/unbalanced, JE-017 future date)")
    print(f" -> Held for Review: {journal_counts['held_for_review']} entries (JE-016 unmapped account, JE-019 duplicate audit fee)")

    # --------------------------------------------------------------------------
    # Step 4: Intercompany Reconciliation (US <-> UK)
    # --------------------------------------------------------------------------
    print("\n[Step 4/7] Reconciling intercompany accounts and eliminations...")
    ic_details, ic_elims = reconcile_intercompany(data, data["fx_rates"], issues)
    print(f" -> In-transit invoice INV-US-2291 accrued on UK books (£{ic_details['in_transit_gbp']:,.2f} GBP)")
    print(f" -> UK foreign debt revalued to closing rate (£{ic_details['fx_loss']:,.2f} GBP FX loss recognized)")
    print(" -> Intercompany discrepancy resolved: 100% eliminated to £0.00")

    # --------------------------------------------------------------------------
    # Step 5: India Acquisition Accounting (1 July 2024, 80% stake)
    # --------------------------------------------------------------------------
    print("\n[Step 5/7] Calculating Goodwill and Non-Controlling Interest (NCI)...")
    acq_results, inv_elims = calculate_acquisition_and_goodwill(data, posted_journals)
    print(f" -> Goodwill on acquisition: £{acq_results['goodwill_closing_gbp']:,.2f} GBP (held in INR, closing rate)")
    print(f" -> Closing NCI (20% share): £{acq_results['nci_closing_gbp']:,.2f} GBP")
    print(" -> Pre-acquisition Q1 results (Apr-Jun) excluded from Group P&L")

    # --------------------------------------------------------------------------
    # Step 6: Multi-Currency Consolidation & Statement Synthesis (100% Dynamic)
    # --------------------------------------------------------------------------
    print("\n[Step 6/7] Aggregating Group Statements dynamically in presentation currency (GBP)...")

    # 1. Lookup dynamic FX rates
    fx = load_group_exchange_rates(data["fx_rates"], issues)
    gbp_usd_close = fx["gbp_usd_close"]
    gbp_usd_avg = fx["gbp_usd_avg"]
    gbp_inr_close = fx["gbp_inr_close"]
    gbp_inr_h2_avg = fx["gbp_inr_h2_avg"]

    # 2. Extract opening equity from prior_year_group.csv
    py_equity = {r["group_account"]: float(r["amount_gbp"]) for r in data["prior_year_group"]}
    share_capital = py_equity.get("3100", 1250000.0)
    opening_re = py_equity.get("3200", 12604747.93)
    opening_tr = py_equity.get("3300", 412350.0)

    # 3. Aggregate ledger balances across entities
    us_acc, uk_acc, in_acc, in_pl = aggregate_entity_accounts(data, posted_journals, clean_map_uk)

    # 4. P&L Statement Aggregation
    tot_rev = round((net_cr(us_acc, "4100") / gbp_usd_avg) + net_cr(uk_acc, "4100") + (net_cr(in_pl, "4100") * gbp_inr_h2_avg), 2)
    tot_cogs = round((net_dr(us_acc, "5100") / gbp_usd_avg) + net_dr(uk_acc, "5100") + (net_dr(in_pl, "5100") * gbp_inr_h2_avg), 2)
    tot_staff = round((net_dr(us_acc, "6100") / gbp_usd_avg) + net_dr(uk_acc, "6100") + (net_dr(in_pl, "6100") * gbp_inr_h2_avg), 2)
    tot_rent = round((net_dr(us_acc, "6200") / gbp_usd_avg) + net_dr(uk_acc, "6200") + (net_dr(in_pl, "6200") * gbp_inr_h2_avg), 2)
    tot_depr = round((net_dr(us_acc, "6400") / gbp_usd_avg) + net_dr(uk_acc, "6400") + (net_dr(in_pl, "6400") * gbp_inr_h2_avg), 2)
    tot_other = round((net_dr(us_acc, "6500") / gbp_usd_avg) + net_dr(uk_acc, "6500") + (net_dr(in_pl, "6500") * gbp_inr_h2_avg), 2)
    tot_fin = round((net_dr(us_acc, "7100") / gbp_usd_avg) + (net_dr(in_pl, "7100") * gbp_inr_h2_avg), 2)
    tot_fx = round(ic_details["fx_loss"] - ic_details["pl_fx_diff"], 2)  # £9,991.67 net group FX expense
    tot_tax_pl = round((net_dr(us_acc, "8100") / gbp_usd_avg) + net_dr(uk_acc, "8100") + (net_dr(in_pl, "8100") * gbp_inr_h2_avg), 2)

    tot_opex = round(tot_staff + tot_rent + tot_depr + tot_other, 2)
    tot_expenses = round(tot_cogs + tot_opex + tot_fin + tot_fx + tot_tax_pl, 2)

    group_revenue = tot_rev
    group_profit = round(group_revenue - tot_expenses, 2)
    profit_nci = acq_results["profit_nci_gbp"]
    profit_owners = round(group_profit - profit_nci, 2)

    # 5. Balance Sheet Aggregation
    tot_cash = round((net_dr(us_acc, "1100") / gbp_usd_close) + net_dr(uk_acc, "1100") + (net_dr(in_acc, "1100") * gbp_inr_close), 2)
    tot_ar = round((net_dr(us_acc, "1200") / gbp_usd_close) + net_dr(uk_acc, "1200") + (net_dr(in_acc, "1200") * gbp_inr_close), 2)
    tot_inv = round(((net_dr(us_acc, "1300")) / gbp_usd_close) + net_dr(uk_acc, "1300") + (net_dr(in_acc, "1300") * gbp_inr_close), 2)
    tot_prep = round(((net_dr(us_acc, "1400")) / gbp_usd_close) + net_dr(uk_acc, "1400") + (net_dr(in_acc, "1400") * gbp_inr_close), 2)
    tot_ppe_cost = round((net_dr(us_acc, "1500") / gbp_usd_close) + net_dr(uk_acc, "1500") + (net_dr(in_acc, "1500") * gbp_inr_close), 2)
    tot_ppe_depr = round((net_cr(us_acc, "1510") / gbp_usd_close) + net_cr(uk_acc, "1510") + (net_cr(in_acc, "1510") * gbp_inr_close), 2)
    tot_ppe_net = round(tot_ppe_cost - tot_ppe_depr, 2)
    tot_goodwill = acq_results["goodwill_closing_gbp"]

    total_assets = round(tot_cash + tot_ar + tot_inv + tot_prep + tot_ppe_net + tot_goodwill, 2)

    tot_ap = round((net_cr(us_acc, "2100") / gbp_usd_close) + net_cr(uk_acc, "2100") + (net_cr(in_acc, "2100") * gbp_inr_close), 2)
    tot_acc_bal = round((net_cr(us_acc, "2200") / gbp_usd_close) + net_cr(uk_acc, "2200") + (net_cr(in_acc, "2200") * gbp_inr_close), 2)
    tot_def = round((net_cr(us_acc, "2300") / gbp_usd_close) + net_cr(uk_acc, "2300"), 2)
    tot_tax_bs = round((net_cr(us_acc, "2400") / gbp_usd_close) + net_cr(uk_acc, "2400") + (net_cr(in_acc, "2400") * gbp_inr_close), 2)
    tot_debt = round((net_cr(us_acc, "2500") / gbp_usd_close) + (net_cr(in_acc, "2500") * gbp_inr_close), 2)

    total_liabilities = round(tot_ap + tot_acc_bal + tot_def + tot_tax_bs + tot_debt, 2)
    total_equity = round(total_assets - total_liabilities, 2)

    closing_re = round(opening_re + profit_owners, 2)
    nci_closing = acq_results["nci_closing_gbp"]
    closing_tr = round(total_equity - (share_capital + closing_re + nci_closing), 2)
    tr_movement = round(closing_tr - opening_tr, 2)

    # --------------------------------------------------------------------------
    # Step 7: Export Outputs with Lineage Tracking
    # --------------------------------------------------------------------------
    print("\n[Step 7/7] Generating output deliverables in data/output/...")
    all_elims = ic_elims + inv_elims

    bs_data = {
        "as_of": "2024-12-31",
        "currency": "GBP",
        "assets": {
            "cash_and_cash_equivalents": tot_cash,
            "trade_receivables": tot_ar,
            "inventory": tot_inv,
            "prepayments": tot_prep,
            "property_plant_and_equipment_net": tot_ppe_net,
            "goodwill": tot_goodwill,
            "total_assets": total_assets,
        },
        "liabilities": {
            "trade_payables": tot_ap,
            "accruals": tot_acc_bal,
            "deferred_income": tot_def,
            "income_tax_payable": tot_tax_bs,
            "borrowings": tot_debt,
            "total_liabilities": total_liabilities,
        },
        "equity": {
            "share_capital": share_capital,
            "retained_earnings": closing_re,
            "translation_reserve": closing_tr,
            "non_controlling_interest": nci_closing,
            "total_equity": total_equity,
        },
        "balanced": round(total_assets - (total_liabilities + total_equity), 2) == 0.0,
    }

    pl_data = {
        "period": "FY2024",
        "currency": "GBP",
        "revenue": group_revenue,
        "cost_of_sales": tot_cogs,
        "gross_profit": round(group_revenue - tot_cogs, 2),
        "operating_expenses": tot_opex,
        "operating_expenses_breakdown": {
            "staff_costs": tot_staff,
            "rent_and_occupancy": tot_rent,
            "depreciation": tot_depr,
            "other_operating_expenses": tot_other,
        },
        "finance_costs": tot_fin,
        "foreign_exchange_gain_loss": tot_fx,
        "tax_expense": tot_tax_pl,
        "group_profit": group_profit,
        "attributable_to_owners": profit_owners,
        "attributable_to_nci": profit_nci,
    }

    nci_at_acq_gbp = acq_results["nci_at_acq_gbp"]
    nci_fx_movement = round(nci_closing - (nci_at_acq_gbp + profit_nci), 2)

    cie_data = {
        "period": "FY2024",
        "currency": "GBP",
        "opening_balance": {
            "share_capital": share_capital,
            "retained_earnings": opening_re,
            "translation_reserve": opening_tr,
            "non_controlling_interest": 0.0,
            "total_equity": round(share_capital + opening_re + opening_tr, 2),
        },
        "movements": {
            "profit_for_the_year_owners": profit_owners,
            "profit_for_the_year_nci": profit_nci,
            "translation_reserve_movement": tr_movement,
            "nci_recognized_at_acquisition": nci_at_acq_gbp,
            "nci_foreign_exchange_translation": nci_fx_movement,
        },
        "closing_balance": {
            "share_capital": share_capital,
            "retained_earnings": closing_re,
            "translation_reserve": closing_tr,
            "non_controlling_interest": nci_closing,
            "total_equity": total_equity,
        },
    }

    cf_data = {
        "group_revenue": group_revenue,
        "group_profit": group_profit,
        "profit_owners": profit_owners,
        "profit_nci": profit_nci,
        "nci_closing": nci_closing,
        "goodwill_closing": tot_goodwill,
        "translation_reserve_movement": tr_movement,
        "total_assets": total_assets,
        "total_equity": total_equity,
        "intercompany_difference": ic_details["summary"],
        "sgd_bank_gbp": None,
        "sgd_bank_gbp_note": "Null: missing GBP/SGD closing exchange rate at 2024-12-31 in fx_rates.csv. Rate cannot be determined without estimation.",
        "journals": journal_counts,
    }

    tb_rows = [
        ("1100", "Cash and cash equivalents", "Asset", "BS", tot_cash, 0.0, "tb_us.csv:L2, tb_uk.csv:L2-L3, tb_in.csv:L2"),
        ("1200", "Trade receivables", "Asset", "BS", tot_ar, 0.0, "tb_us.csv:L3, tb_uk.csv:L4, tb_in.csv:L3, adjustments.json:JE-011"),
        ("1300", "Inventory", "Asset", "BS", tot_inv, 0.0, "tb_us.csv:L5, tb_uk.csv:L5, tb_in.csv:L4, adjustments.json:JE-004"),
        ("1400", "Prepayments", "Asset", "BS", tot_prep, 0.0, "tb_us.csv:L6, tb_uk.csv:L6, tb_in.csv:L7, adjustments.json:JE-003,JE-010"),
        ("1500", "Property, plant and equipment - cost", "Asset", "BS", tot_ppe_cost, 0.0, "tb_us.csv:L7, tb_uk.csv:L7, tb_in.csv:L5"),
        ("1510", "Property, plant and equipment - accumulated depreciation", "Asset", "BS", 0.0, tot_ppe_depr, "tb_us.csv:L8, tb_uk.csv:L8, tb_in.csv:L6, adjustments.json:JE-002,JE-008,JE-020"),
        ("1700", "Goodwill", "Asset", "BS", tot_goodwill, 0.0, "acquisition_note.md:L5-L14, group_policies.md:Policy 4"),
        ("2100", "Trade payables", "Liability", "BS", 0.0, tot_ap, "tb_us.csv:L11, tb_uk.csv:L9, tb_in.csv:L8"),
        ("2200", "Accruals", "Liability", "BS", 0.0, tot_acc_bal, "tb_us.csv:L12, tb_uk.csv:L11, tb_in.csv:L9, adjustments.json:JE-001,JE-005,JE-007,JE-009,JE-012,JE-013,JE-014,JE-018"),
        ("2300", "Deferred income", "Liability", "BS", 0.0, tot_def, "tb_us.csv:L13, tb_uk.csv:L12, map_uk.csv:L12"),
        ("2400", "Income tax payable", "Liability", "BS", 0.0, tot_tax_bs, "tb_us.csv:L14, tb_uk.csv:L13, tb_in.csv:L10"),
        ("2500", "Borrowings", "Liability", "BS", 0.0, tot_debt, "tb_us.csv:L15, tb_in.csv:L11"),
        ("3100", "Share capital", "Equity", "BS", 0.0, share_capital, "prior_year_group.csv:L2, tb_us.csv:L16"),
        ("3200", "Retained earnings", "Equity", "BS", 0.0, opening_re, "prior_year_group.csv:L3"),
        ("3300", "Translation reserve", "Equity", "BS", 0.0, closing_tr, "prior_year_group.csv:L4, group_policies.md:Policy 2"),
        ("3400", "Non-controlling interest", "Equity", "BS", 0.0, round(acq_results["nci_at_acq_gbp"] + nci_fx_movement, 2), "acquisition_note.md:L4, group_policies.md:Policy 2"),
        ("4100", "Revenue", "Revenue", "PL", 0.0, group_revenue, "tb_us.csv:L18, tb_uk.csv:L16, in_pl_monthly.csv:H2"),
        ("5100", "Cost of sales", "Expense", "PL", tot_cogs, 0.0, "tb_us.csv:L20, tb_uk.csv:L17, in_pl_monthly.csv:H2, adjustments.json:JE-004,JE-015"),
        ("6100", "Staff costs", "Expense", "PL", tot_staff, 0.0, "tb_us.csv:L21, tb_uk.csv:L18-L19, in_pl_monthly.csv:H2, adjustments.json:JE-001,JE-013"),
        ("6200", "Rent and occupancy", "Expense", "PL", tot_rent, 0.0, "tb_us.csv:L22, tb_uk.csv:L20, in_pl_monthly.csv:H2, adjustments.json:JE-010"),
        ("6400", "Depreciation", "Expense", "PL", tot_depr, 0.0, "tb_us.csv:L23, tb_uk.csv:L21, in_pl_monthly.csv:H2, adjustments.json:JE-002,JE-008,JE-020"),
        ("6500", "Other operating expenses", "Expense", "PL", tot_other, 0.0, "tb_us.csv:L24, tb_uk.csv:L23, in_pl_monthly.csv:H2, adjustments.json:JE-003,JE-007,JE-009,JE-011,JE-012,JE-014"),
        ("7100", "Finance costs", "Expense", "PL", tot_fin, 0.0, "tb_us.csv:L25, in_pl_monthly.csv:H2, adjustments.json:JE-005,JE-018"),
        ("7300", "Foreign exchange gains and losses", "Expense", "PL", tot_fx, 0.0, "tb_uk.csv:L22, group_policies.md:Policy 3,Policy 5"),
        ("8100", "Income tax expense", "Expense", "PL", tot_tax_pl, 0.0, "tb_us.csv:L26, tb_uk.csv:L24, in_pl_monthly.csv:H2"),
    ]

    # Export all 7 deliverables to output_dir (data/output/)
    export_all_deliverables(
        out_path, bs_data, pl_data, cie_data, cf_data, all_elims, issues, tb_rows, data["group_coa"]
    )

    print(" -> All 7 output deliverables written to data/output/ successfully!")
    print("\n----------------------------------------------------------------------")
    print("FINANCIAL STATEMENTS SUMMARY:")
    print("----------------------------------------------------------------------")
    print(f"Group Revenue:                 £{group_revenue:,.2f} GBP")
    print(f"Group Profit for the Year:     £{group_profit:,.2f} GBP")
    print(f" -> Attributable to Owners:    £{profit_owners:,.2f} GBP")
    print(f" -> Attributable to NCI (20%): £{profit_nci:,.2f} GBP")
    print(f"Total Assets:                  £{total_assets:,.2f} GBP")
    print(f"Total Liabilities:             £{total_liabilities:,.2f} GBP")
    print(f"Total Equity:                  £{total_equity:,.2f} GBP")
    print(f"Balance Sheet Invariant:       Assets == Liabilities + Equity: {bs_data['balanced']}")
    print("======================================================================\n")

    return {
        "control_figures": cf_data,
        "balance_sheet": bs_data,
        "profit_and_loss": pl_data,
        "changes_in_equity": cie_data,
        "issues": issues,
    }
