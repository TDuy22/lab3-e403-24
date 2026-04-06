from src.tools.data import ALLOWED_CITIES, SHIPPING_BASE_VND, SHIPPING_PER_KG_VND


def calc_shipping(weight_kg: float, destination: str) -> str:
    dest = destination.strip().lower()
    if dest not in ALLOWED_CITIES:
        return (
            "error=unknown_destination, destination="
            f"{destination.strip()}, allowed=Hanoi|HCMC|Da Nang"
        )
    if weight_kg < 0:
        return "error=invalid_weight, message=weight_kg_must_be_non_negative"

    fee = SHIPPING_BASE_VND + (weight_kg * SHIPPING_PER_KG_VND)
    return f"destination={destination.strip()}, weight_kg={weight_kg}, shipping_fee_vnd={int(fee)}"
