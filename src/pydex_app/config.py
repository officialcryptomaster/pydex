import os
import pydex_app.utils as pdu

NULL_ADDRESS = "0x0000000000000000000000000000000000000000"

class PydexBaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "development secret key is not safe")
    SQLALCHEMY_DATABASE_URI = "sqlite:///../../pydex.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # PYDEX EXCHANGE PARAMS
    PYDEX_NETWORK_ID = "4"  # RINKEBY 
    PYDEX_ZRX_FEE_RECIPIENT = NULL_ADDRESS
    PYDEX_ZRX_MAKER_FEE = pdu.to_base_unit_amount(0)
    PYDEX_ZRX_TAKER_FEE = pdu.to_base_unit_amount(0)
    PYDEX_WHITELISTED_TOKENS = "*"
    # GUI DEFAULT PARAMS
    OB_DEFAULT_PAGE = 1
    OB_DEFAULT_PER_PAGE = 20
