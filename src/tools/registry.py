from src.tools.inventory import check_stock
from src.tools.coupons import get_discount
from src.tools.shipping import calc_shipping

TOOLS = [
    {
        "name": "check_stock",
        "description": (
            "Get stock, unit price (VND), and weight per unit for an item. "
            "Input: item_name (string). Example: check_stock('iPhone'). "
            "Output keys: item, in_stock, unit_price_vnd, weight_kg_per_unit. "
            "If unknown: returns error=unknown_item."
        ),
        "func": check_stock,
    },
    {
        "name": "get_discount",
        "description": (
            "Get discount percent for a coupon code. "
            "Input: coupon_code (string). Example: get_discount('WINNER') or get_discount('NONE'). "
            "Output keys: coupon, discount_percent. If invalid: error=unknown_coupon."
        ),
        "func": get_discount,
    },
    {
        "name": "calc_shipping",
        "description": (
            "Compute shipping fee (VND) using total weight in kg and destination city. "
            "Input: weight_kg (float), destination (string). Example: calc_shipping(0.48, 'Hanoi'). "
            "Allowed destinations: Hanoi, HCMC, Da Nang. Output keys: shipping_fee_vnd."
        ),
        "func": calc_shipping,
    },
]
