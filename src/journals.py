"""
Journal Processing Engine (src/journals.py)

Filters and validates year-end manual adjustments (the 20 journals):
- Posts valid FY2024 double-entry adjustments (16 posted)
- Blocks prompt injections and unbalanced entries (JE-006)
- Blocks future out-of-period entries (JE-017)
- Holds unmapped accounts (JE-016) and suspected duplicate fees (JE-019) for review
"""

from typing import Any, Dict, List, Tuple
from src.validation import detect_prompt_injection


def process_journal_adjustments(
    adjustments: List[Dict[str, Any]],
    valid_accounts_by_entity: Dict[str, List[str]],
    issues: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Evaluates each adjustment entry against strict accounting and security rules.
    Returns:
        (posted_journals, status_counts_dict)
    """
    posted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    held_for_review: List[Dict[str, Any]] = []

    seen_fingerprints: Dict[Tuple[str, float, Tuple[str, ...], Tuple[str, ...]], str] = {}

    for entry in adjustments:
        entry_id = entry["id"]
        entity = entry["entity"]
        date = str(entry.get("date", ""))
        desc = entry.get("description", "")
        lines = entry.get("lines", [])

        # 1. Prompt Injection Defense
        has_injection = any(
            detect_prompt_injection(line.get("memo")) for line in lines
        ) or detect_prompt_injection(desc)

        # 2. Accounting Balance Verification: Debit == Credit
        tot_debit = round(sum(line["debit"] for line in lines), 2)
        tot_credit = round(sum(line["credit"] for line in lines), 2)
        is_balanced = (tot_debit == tot_credit)

        if has_injection or not is_balanced:
            reasons = []
            if has_injection:
                reasons.append("Prompt injection attack detected in memo")
            if not is_balanced:
                diff = abs(tot_debit - tot_credit)
                reasons.append(
                    f"Unbalanced journal entry (Dr={tot_debit:.2f}, Cr={tot_credit:.2f}, Diff={diff:.2f})"
                )
            issues.append({
                "file": "adjustments.json",
                "line": entry.get("line_num"),
                "item_id": entry_id,
                "amount_affected": max(tot_debit, tot_credit),
                "action_taken": "blocked",
                "description": f"{entry_id} rejected: {'; '.join(reasons)}",
            })
            rejected.append(entry)
            continue

        # 3. Accounting Period Verification (Must be FY2024)
        if not date.startswith("2024"):
            issues.append({
                "file": "adjustments.json",
                "line": entry.get("line_num"),
                "item_id": entry_id,
                "amount_affected": tot_debit,
                "action_taken": "blocked",
                "description": f"{entry_id} rejected: Out-of-period transaction date '{date}' (not FY2024)",
            })
            rejected.append(entry)
            continue

        # 4. Valid Chart of Accounts Existence
        entity_valid_accounts = valid_accounts_by_entity.get(entity, [])
        unmapped_accounts = [
            line["account"]
            for line in lines
            if line["account"] not in entity_valid_accounts
        ]
        if unmapped_accounts:
            issues.append({
                "file": "adjustments.json",
                "line": entry.get("line_num"),
                "item_id": entry_id,
                "amount_affected": tot_debit,
                "action_taken": "flagged",
                "description": f"{entry_id} held for review: Contains unmapped/unknown accounts: {unmapped_accounts}",
            })
            held_for_review.append(entry)
            continue

        # 5. Duplicate Detection via Financial Fingerprint (Entity, Amount, Dr Accounts, Cr Accounts)
        dr_accs = tuple(sorted(l["account"] for l in lines if l["debit"] > 0))
        cr_accs = tuple(sorted(l["account"] for l in lines if l["credit"] > 0))
        fingerprint = (entity, round(tot_debit, 2), dr_accs, cr_accs)

        if fingerprint in seen_fingerprints:
            orig_id = seen_fingerprints[fingerprint]
            issues.append({
                "file": "adjustments.json",
                "line": entry.get("line_num"),
                "item_id": entry_id,
                "amount_affected": tot_debit,
                "action_taken": "flagged",
                "description": (
                    f"{entry_id} held for review: Suspected duplicate of previously submitted journal {orig_id} ({desc})"
                ),
            })
            held_for_review.append(entry)
            continue

        # Valid journal posted
        seen_fingerprints[fingerprint] = entry_id
        posted.append(entry)

    counts = {
        "posted": len(posted),
        "rejected": len(rejected),
        "held_for_review": len(held_for_review),
        "total": len(adjustments),
    }
    return posted, counts
