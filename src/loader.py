"""
Data Loader Module (src/loader.py)

Reads raw CSV, JSON, and Markdown files from data/input/ into clean Python dictionaries.
Preserves line numbers (row_num) for end-to-end audit traceability.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Union


def load_csv_rows(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Reads a CSV file and returns a list of row dictionaries with row numbers."""
    rows = []
    file_path = Path(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_num, row in enumerate(reader, start=2):  # Line 1 is header
            cleaned_row = dict(row)
            cleaned_row["row_num"] = line_num
            rows.append(cleaned_row)
    return rows


def load_all_data(input_dir: Union[str, Path]) -> Dict[str, Any]:
    """
    Loads all ERP source files into a single master dictionary.
    Supports data/input or data/ root seamlessly.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        # Fallback to parent/data or data/input
        if (input_path / "input").exists():
            input_path = input_path / "input"
        elif (Path("data/input")).exists():
            input_path = Path("data/input")
        elif (Path("data")).exists():
            input_path = Path("data")

    data: Dict[str, Any] = {}

    # 1. Entity Master
    data["entities"] = load_csv_rows(input_path / "entities.csv")

    # 2. Group Chart of Accounts (COA)
    coa_rows = load_csv_rows(input_path / "group_coa.csv")
    data["group_coa"] = {r["account_code"]: r for r in coa_rows}

    # 3. Chart of Accounts Mappings
    uk_map_rows = load_csv_rows(input_path / "map_uk.csv")
    data["map_uk"] = {r["local_code"]: r["group_code"] for r in uk_map_rows}

    in_map_rows = load_csv_rows(input_path / "map_in.csv")
    data["map_in"] = {r["local_code"]: r["group_code"] for r in in_map_rows}

    # 4. Exchange Rates
    fx_rows = load_csv_rows(input_path / "fx_rates.csv")
    for r in fx_rows:
        r["rate"] = float(r["rate"])
    data["fx_rates"] = fx_rows

    # 5. Entity Trial Balances
    us_rows = load_csv_rows(input_path / "tb_us.csv")
    for r in us_rows:
        r["debit"] = float(r["debit"])
        r["credit"] = float(r["credit"])
    data["tb_us"] = us_rows

    uk_rows = load_csv_rows(input_path / "tb_uk.csv")
    for r in uk_rows:
        r["balance"] = float(r["balance"])
        r["txn_amount"] = float(r["txn_amount"]) if r.get("txn_amount") else None
    data["tb_uk"] = uk_rows

    in_rows = load_csv_rows(input_path / "tb_in.csv")
    for r in in_rows:
        r["amount"] = float(r["amount"])
    data["tb_in"] = in_rows

    # 6. India Monthly P&L
    monthly_rows = load_csv_rows(input_path / "in_pl_monthly.csv")
    for r in monthly_rows:
        r["amount"] = float(r["amount"])
    data["in_pl_monthly"] = monthly_rows

    # 7. Intercompany Invoices
    ic_rows = load_csv_rows(input_path / "intercompany.csv")
    for r in ic_rows:
        r["doc_amount"] = float(r["doc_amount"])
        r["booked_amount"] = float(r["booked_amount"])
    data["intercompany"] = ic_rows

    # 8. Subledger Controls
    subledger_rows = load_csv_rows(input_path / "subledger_controls.csv")
    for r in subledger_rows:
        r["control_total"] = float(r["control_total"])
    data["subledger_controls"] = subledger_rows

    # 9. Prior Year Group Equity
    py_rows = load_csv_rows(input_path / "prior_year_group.csv")
    for r in py_rows:
        r["amount_gbp"] = float(r["amount_gbp"])
    data["prior_year_group"] = py_rows

    # 10. Manual Adjustments JSON
    adj_file = input_path / "adjustments.json"
    with open(adj_file, "r", encoding="utf-8") as f:
        adj_content = f.read()
        adj_data = json.loads(adj_content)
        
        entry_lines = {}
        for l_idx, l_str in enumerate(adj_content.splitlines(), start=1):
            import re
            m = re.search(r'"id":\s*"(JE-\d+)"', l_str)
            if m:
                entry_lines[m.group(1)] = l_idx

        for entry in adj_data.get("entries", []):
            entry["line_num"] = entry_lines.get(entry.get("id"))
            for line in entry.get("lines", []):
                line["debit"] = float(line["debit"])
                line["credit"] = float(line["credit"])
        data["adjustments"] = adj_data.get("entries", [])

    data["input_dir"] = input_path
    return data
