"""
Put all pyDEX app configs here

author: officialcryptomaster@gmail.com
"""

import os
from zero_ex.contract_addresses import NetworkId
from utils.web3utils import to_base_unit_amount, NULL_ADDRESS


class PydexBaseConfig:  # pylint: disable=too-few-public-methods
    """Base configuration class for pyDEX App"""
    SECRET_KEY = os.environ.get("SECRET_KEY", "development secret key is not safe")
    SQLALCHEMY_DATABASE_URI = "sqlite:///{}".format(
        os.environ.get("PYDEX_DB_PATH") or "{}/pydex.db".format(os.getcwd()))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False
    # PYDEX EXCHANGE PARAMS
    PYDEX_NETWORK_ID = NetworkId.RINKEBY.value
    PYDEX_ZX_FEE_RECIPIENT = NULL_ADDRESS
    PYDEX_ZX_MAKER_FEE = to_base_unit_amount(0)
    PYDEX_ZX_TAKER_FEE = to_base_unit_amount(0)
    PYDEX_WHITELISTED_TOKENS = "*"
    # GUI DEFAULT PARAMS
    OB_DEFAULT_PAGE = 1
    OB_DEFAULT_PER_PAGE = 20
