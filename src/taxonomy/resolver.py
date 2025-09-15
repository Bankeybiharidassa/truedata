CATEGORY_ORDER = [
    "Sub-sub-sub-sub-sub category",
    "Sub-sub-sub-sub category",
    "Sub-sub-sub category",
    "Sub-sub category",
    "Sub category",
    "Root category",
]

def deepest_category(row: dict) -> str:
    """Return the deepest non-empty category for a given CSV row."""
    for col in CATEGORY_ORDER:
        v = (row.get(col) or "").strip()
        if v:
            return v
    return (row.get("Root category") or "").strip()
