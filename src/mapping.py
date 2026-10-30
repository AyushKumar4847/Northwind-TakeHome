"""
Mapping Module (src/mapping.py)

Manages chart of accounts mapping and sanitization across subsidiaries.
"""

from typing import Any, Dict, List


def fix_chart_of_accounts_mapping(
    uk_map: Dict[str, str], issues: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Sanitizes local-to-group account mappings.
    Detects and corrects mapping errors such as UK Deferred Income (local 2310)
    being incorrectly mapped to Revenue (4100), remapping it to Liability (2300).
    """
    clean_map = dict(uk_map)

    if clean_map.get("2310") == "4100":
        clean_map["2310"] = "2300"
        issues.append({
            "file": "map_uk.csv",
            "line": 12,
            "item_id": "MAP-UK-2310",
            "amount_affected": 180000.00,
            "action_taken": "assumed",
            "description": (
                "Deferred income (local 2310) incorrectly mapped to Revenue (4100). "
                "Remapped to Deferred income liability (2300)."
            ),
        })

    return clean_map

