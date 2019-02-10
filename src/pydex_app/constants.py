"""
Put all application constant here

author: officialcryptomaster@gmail.com
"""
from decimal import Decimal

NULL_ADDRESS = "0x0000000000000000000000000000000000000000"

ZERO = Decimal(0)
ZERO_STR = "0"
MAX_INT = Decimal(2) ** 256
MAX_INT_STR = "{:.0f}".format(MAX_INT)

MAIN_NETWORK_ID = "1"
RINKEBY_NETWORK_ID = "4"
KOVAN_NETWORK_ID = "42"
GANACHE_NETWORK_ID = "50"
