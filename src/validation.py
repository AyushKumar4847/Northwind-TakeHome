"""
Validation & Security Module (src/validation.py)

Performs:
1. Adversarial prompt injection defense on transaction memos.
2. Double-entry trial balance equilibrium verification (Debit == Credit).
3. Subledger control total reconciliations (Accounts Receivable & Accounts Payable).
"""

import re
from typing import Any, Dict, List, Optional


def detect_prompt_injection(text: Optional[str]) -> bool:
    """
    Scans transaction memos and descriptions for adversarial prompt injection phrases.
    Attackers attempt to deceive automated review agents with phrases like
    'skip the balance check' or 'pre-approved by the CFO'.
    """
    if not text:
        return False

    suspicious_patterns = [
        r"automated reviewers",
        r"skip the .*check",
        r"do not list",
        r"pre-approved by the cfo",
        r"ignore previous instructions",
    ]
    lowered = text.lower()
    return any(re.search(pat, lowered) for pat in suspicious_patterns)


def validate_trial_balances_and_subledgers(
    data: Dict[str, Any], issues: List[Dict[str, Any]]
) -> bool:
    """
    Validates trial balance mathematical equilibrium and audits subledgers against general ledgers.
    """
    # 1. US NetSuite Trial Balance Check
    us_debits = sum(r["debit"] for r in data["tb_us"])
    us_credits = sum(r["credit"] for r in data["tb_us"])
    if round(us_debits - us_credits, 2) != 0.0:
        issues.append({
            "file": "tb_us.csv",
            "line": None,
            "item_id": "TB-US-UNBALANCED",
            "amount_affected": round(us_debits - us_credits, 2),
            "action_taken": "blocked",
            "description": f"US TB out of balance: Dr={us_debits:.2f}, Cr={us_credits:.2f}",
        })

    # 2. UK Sage 50 Trial Balance Check
    uk_balance_sum = sum(r["balance"] for r in data["tb_uk"])
    if round(uk_balance_sum, 2) != 0.0:
        issues.append({
            "file": "tb_uk.csv",
            "line": None,
            "item_id": "TB-UK-UNBALANCED",
            "amount_affected": round(uk_balance_sum, 2),
            "action_taken": "blocked",
            "description": f"UK TB out of balance: Sum={uk_balance_sum:.2f}",
        })

    # 3. India Tally Prime Trial Balance Check
    in_debits = sum(r["amount"] for r in data["tb_in"] if r["dr_cr"] == "Dr")
    in_credits = sum(r["amount"] for r in data["tb_in"] if r["dr_cr"] == "Cr")
    if round(in_debits - in_credits, 2) != 0.0:
        issues.append({
            "file": "tb_in.csv",
            "line": None,
            "item_id": "TB-IN-UNBALANCED",
            "amount_affected": round(in_debits - in_credits, 2),
            "action_taken": "blocked",
            "description": f"India TB out of balance: Dr={in_debits:.2f}, Cr={in_credits:.2f}",
        })

    # 4. Subledger Control Reconciliations (AR & AP)
    for ctrl in data["subledger_controls"]:
        entity = ctrl["entity_id"]
        ledger = ctrl["ledger"]
        control_total = ctrl["control_total"]

        if entity == "US":
            code = "1200" if "receivable" in ledger.lower() else "2100"
            gl_row = next((r for r in data["tb_us"] if r["account_code"] == code), None)
            gl_amount = gl_row["debit"] if code == "1200" else gl_row["credit"] if gl_row else 0.0
            line_no = gl_row["row_num"] if gl_row else ctrl["row_num"]
        elif entity == "UK":
            code = "1100" if "receivable" in ledger.lower() else "2100"
            gl_row = next((r for r in data["tb_uk"] if r["nominal_code"] == code), None)
            gl_amount = abs(gl_row["balance"]) if gl_row else 0.0
            line_no = ctrl["row_num"]
        elif entity == "IN":
            code = "IN-AR" if "receivable" in ledger.lower() else "IN-AP"
            gl_row = next((r for r in data["tb_in"] if r["ledger_code"] == code), None)
            gl_amount = gl_row["amount"] if gl_row else 0.0
            line_no = gl_row["row_num"] if gl_row else ctrl["row_num"]
        else:
            continue

        variance = round(gl_amount - control_total, 2)
        if variance != 0.0:
            issues.append({
                "file": "subledger_controls.csv",
                "line": line_no,
                "item_id": f"{entity}-{code}",
                "amount_affected": abs(variance),
                "action_taken": "flagged",
                "description": (
                    f"{entity} {ledger} mismatch: GL={gl_amount:.2f}, Control={control_total:.2f}, Variance={variance:.2f}"
                ),
            })

    return True

