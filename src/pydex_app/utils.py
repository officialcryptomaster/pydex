from decimal import Decimal

ZERO = Decimal(0)
ZERO_STR = "0"
MAX_INT = Decimal(2) ** 256
MAX_INT_STR = "{:.0f}".format(MAX_INT)


def to_base_unit_amount(amount, decimals=18):
    return "{:f}".format(Decimal(amount) ** decimals)
