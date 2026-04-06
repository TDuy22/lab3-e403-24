from src.tools import TOOLS
from src.tools.coupons import get_discount
from src.tools.data import ALLOWED_CITIES, CATALOG, COUPONS
from src.tools.inventory import check_stock
from src.tools.shipping import calc_shipping


def test_catalog_structure():
    assert len(CATALOG) >= 5  # expanded catalog has many items
    # Spot-check structure of one item
    sample_key = "iphone_15_pro"
    assert sample_key in CATALOG
    sample = CATALOG[sample_key]
    assert sample["unit_price_vnd"] == 30_000_000
    assert sample["weight_kg_per_unit"] == 0.21
    assert "display_name" in sample
    assert "stock" in sample


def test_coupons_structure():
    assert COUPONS["WINNER"] == 15
    assert COUPONS["SAVE10"] == 10


def test_allowed_cities():
    assert "hanoi" in ALLOWED_CITIES
    assert len(ALLOWED_CITIES) == 3


def test_check_stock_valid():
    # "iPhone 15 Pro" -> _normalize -> "iphone15pro" -> matches catalog key "iphone_15_pro"
    result = check_stock("iPhone 15 Pro")
    assert "item=iPhone 15 Pro" in result
    assert "in_stock=25" in result
    assert "unit_price_vnd=30000000" in result
    assert "weight_kg_per_unit=0.21" in result


def test_check_stock_normalization():
    """
    Verify fuzzy normalization: all variants below must resolve to the same item.
    _normalize strips ALL non-alphanumeric chars and lowercases.
    """
    variants = [
        "Xiaomi 14",    # spaced -> "xiaomi14"
        "xiao mi 14",   # extra space inside brand -> "xiaomi14" (key point)
        "xiaomi-14",    # hyphen -> "xiaomi14"
        "XIAOMI_14",    # uppercase + underscore -> "xiaomi14"
        "Xiaomi14",     # no separator -> "xiaomi14"
    ]
    for variant in variants:
        result = check_stock(variant)
        assert "error" not in result, f"Expected match for '{variant}', got: {result}"
        assert "item=Xiaomi 14" in result, f"Wrong item for '{variant}': {result}"


def test_check_stock_invalid():
    result = check_stock("Nintendo")
    assert "error=unknown_item" in result
    assert "item_name=Nintendo" in result


def test_get_discount_valid():
    result = get_discount("WINNER")
    assert "coupon=WINNER" in result
    assert "discount_percent=15" in result


def test_get_discount_none():
    assert "discount_percent=0" in get_discount("")
    assert "discount_percent=0" in get_discount("none")


def test_get_discount_invalid():
    result = get_discount("FREE100")
    assert "error=unknown_coupon" in result


def test_calc_shipping_valid():
    result = calc_shipping(0.48, "Hanoi")
    assert "destination=Hanoi" in result
    assert "weight_kg=0.48" in result
    assert "shipping_fee_vnd=39600" in result


def test_calc_shipping_formula():
    result = calc_shipping(1.2, "HCMC")
    assert "shipping_fee_vnd=54000" in result


def test_calc_shipping_invalid_dest():
    result = calc_shipping(0.5, "Tokyo")
    assert "error=unknown_destination" in result


def test_calc_shipping_negative_weight():
    result = calc_shipping(-1, "Hanoi")
    assert "error=invalid_weight" in result


def test_tools_registry_structure():
    assert isinstance(TOOLS, list)
    assert len(TOOLS) == 3

    names = [t["name"] for t in TOOLS]
    assert "check_stock" in names
    assert "get_discount" in names
    assert "calc_shipping" in names

    for tool in TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "func" in tool
        assert callable(tool["func"])


def test_import_from_tools():
    assert len(TOOLS) == 3


def test_happy_path_math_components():
    stock = check_stock("iPhone 15 Pro")
    assert "unit_price_vnd=30000000" in stock

    discount = get_discount("WINNER")
    assert "discount_percent=15" in discount

    shipping = calc_shipping(0.48, "Hanoi")
    assert "shipping_fee_vnd=39600" in shipping  # 30000 + 0.48*20000 = 39600


def test_output_single_line_key_value_contract():
    samples = [
        check_stock("iPhone 15 Pro"),  # valid — normalizes to iphone_15_pro
        check_stock("Unknown"),
        get_discount("WINNER"),
        get_discount("NONE"),
        get_discount("BAD"),
        calc_shipping(0.48, "Hanoi"),
        calc_shipping(-1, "Hanoi"),
        calc_shipping(0.5, "Tokyo"),
    ]

    for output in samples:
        assert "\n" not in output
        tokens = [p.strip() for p in output.split(",")]
        assert all("=" in token for token in tokens)
