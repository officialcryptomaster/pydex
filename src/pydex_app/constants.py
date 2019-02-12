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

NETWORK_INFO = {
    MAIN_NETWORK_ID: {
        "name": "main",
        # "exchange_id": "",
    },
    RINKEBY_NETWORK_ID: {
        "name": "rinkeby",
        "exchange_id": "0xbce0b5f6eb618c565c3e5f5cd69652bbc279f44e",
    },
    KOVAN_NETWORK_ID: {
        "name": "kovan",
        # "exchange_id": "",
    },
    GANACHE_NETWORK_ID: {
        "name": "ganache",
        # "exchange_id": "",
    },
}
