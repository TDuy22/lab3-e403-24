from src.tools.data import COUPONS


def get_discount(coupon_code: str) -> str:
    code = coupon_code.strip().upper()
    if code in {"", "NONE"}:
        return "coupon=NONE, discount_percent=0"
    if code not in COUPONS:
        valid = "|".join(sorted(COUPONS.keys()))
        return f"error=unknown_coupon, coupon={code}, valid={valid}"
    return f"coupon={code}, discount_percent={COUPONS[code]}"
