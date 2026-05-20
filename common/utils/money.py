def paise_to_rupees(paise: int) -> str:
    return f"{paise / 100:.2f}"


def rupees_to_paise(rupees: float | str) -> int:
    return int(round(float(rupees) * 100))
