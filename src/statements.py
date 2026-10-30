"""
Financial Statements & Exporter Module (src/statements.py)

Generates structured JSON statements and CSV audit reports:
1. balance_sheet.json
2. profit_and_loss.json
3. changes_in_equity.json
4. control_figures_ak.json (and control_figures.json)
5. eliminations.csv
6. issues.json
7. consolidated_tb.csv
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def export_all_deliverables(
    output_dir: Path,
    bs_data: Dict[str, Any],
    pl_data: Dict[str, Any],
    cie_data: Dict[str, Any],
    cf_data: Dict[str, Any],
    all_elims: List[Dict[str, Any]],
    issues: List[Dict[str, Any]],
    tb_rows: List[tuple],
    group_coa: Dict[str, Any],
) -> None:
    """Writes all 7 required deliverables to the output directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. eliminations.csv
    with open(output_dir / "eliminations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["entry_id", "entity", "reference", "group_account", "account_name", "description", "debit_gbp", "credit_gbp", "source_rows"])
        for e in all_elims:
            acc_name = group_coa.get(e["account"], {}).get("account_name", "")
            entity = e.get("entity", "")
            ref = e.get("ref", e.get("entry_id", ""))
            writer.writerow([e["entry_id"], entity, ref, e["account"], acc_name, e["desc"], f"{e['debit']:.2f}", f"{e['credit']:.2f}", e["sources"]])

    # 2. issues.json
    with open(output_dir / "issues.json", "w", encoding="utf-8") as f:
        json.dump(issues, f, indent=2)

    # 3. balance_sheet.json
    with open(output_dir / "balance_sheet.json", "w", encoding="utf-8") as f:
        json.dump(bs_data, f, indent=2)

    # 4. profit_and_loss.json
    with open(output_dir / "profit_and_loss.json", "w", encoding="utf-8") as f:
        json.dump(pl_data, f, indent=2)

    # 5. changes_in_equity.json
    with open(output_dir / "changes_in_equity.json", "w", encoding="utf-8") as f:
        json.dump(cie_data, f, indent=2)

    # 6. control_figures_ak.json
    with open(output_dir / "control_figures_ak.json", "w", encoding="utf-8") as f:
        json.dump(cf_data, f, indent=2)

    # 7. consolidated_tb.csv
    with open(output_dir / "consolidated_tb.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["account_code", "account_name", "account_type", "statement", "debit_gbp", "credit_gbp", "net_balance_gbp", "source_rows"])
        for code, name, atype, stmt, dr, cr, sources in tb_rows:
            net = dr - cr
            writer.writerow([code, name, atype, stmt, f"{dr:.2f}", f"{cr:.2f}", f"{net:.2f}", sources])

