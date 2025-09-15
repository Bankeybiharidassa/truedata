import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from taxonomy.resolver import deepest_category


def test_deepest_category_prefers_deepest_non_empty():
    row = {
        "Root category": "Root",
        "Sub category": "Sub",
        "Sub-sub category": "",
        "Sub-sub-sub category": "",
        "Sub-sub-sub-sub category": "Deep",
        "Sub-sub-sub-sub-sub category": "",
    }
    assert deepest_category(row) == "Deep"

def test_deepest_category_fallback_to_root():
    row = {
        "Root category": "Root",
        "Sub category": "",
        "Sub-sub category": "",
        "Sub-sub-sub category": "",
        "Sub-sub-sub-sub category": "",
        "Sub-sub-sub-sub-sub category": "",
    }
    assert deepest_category(row) == "Root"
