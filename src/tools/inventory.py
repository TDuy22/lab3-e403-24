from src.tools.data import CATALOG


def check_stock(item_name: str) -> str:
    key = item_name.strip().lower()
    if key not in CATALOG:
        known = "|".join(v["display_name"] for v in CATALOG.values())
        return f"error=unknown_item, item_name={item_name.strip()}, known_items={known}"

    row = CATALOG[key]
    return (
        f"item={row['display_name']}, in_stock={row['stock']}, "
        f"unit_price_vnd={row['unit_price_vnd']}, weight_kg_per_unit={row['weight_kg_per_unit']}"
    )
