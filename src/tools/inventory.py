import re
from typing import Dict

from pydantic import BaseModel, field_validator

from src.tools.data import CATALOG


def _normalize(text: str) -> str:
    """
    Normalize a string for fuzzy catalog matching:
    - lowercase
    - strip ALL non-alphanumeric characters (spaces, underscores, hyphens, dots, etc.)

    Examples:
        "iPhone 15 Pro"  -> "iphone15pro"
        "iphone_15_pro"  -> "iphone15pro"
        "xiao mi 14"     -> "xiaomi14"
        "Xiaomi-14"      -> "xiaomi14"
    """
    return re.sub(r"[^a-z0-9]", "", text.lower())


# Pre-compute normalized lookup table at module load (O(1) lookup at runtime).
# Maps normalized_key -> original row dict from CATALOG.
_CATALOG_NORM: Dict[str, dict] = {
    _normalize(k): v for k, v in CATALOG.items()
}


class StockQuery(BaseModel):
    """
    Pydantic model that normalizes item_name on construction,
    ensuring consistent matching regardless of spacing or casing.
    """
    item_name: str

    @field_validator("item_name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return _normalize(v.strip())


def check_stock(item_name: str) -> str:
    query = StockQuery(item_name=item_name)
    norm_key = query.item_name

    if norm_key not in _CATALOG_NORM:
        known = "|".join(v["display_name"] for v in _CATALOG_NORM.values())
        return f"error=unknown_item, item_name={item_name.strip()}, known_items={known}"

    row = _CATALOG_NORM[norm_key]
    return (
        f"item={row['display_name']}, in_stock={row['stock']}, "
        f"unit_price_vnd={row['unit_price_vnd']}, weight_kg_per_unit={row['weight_kg_per_unit']}"
    )
