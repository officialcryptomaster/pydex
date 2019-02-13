"""
Fixtures for pytest

author: originalcryptomaster@gmail.com
"""

import os
import tempfile

import binascii
from decimal import Decimal
import time
import pytest

from web3 import Web3, HTTPProvider
from zero_ex.json_schemas import assert_valid

from pydex_app import create_app
from pydex_app.config import PydexBaseConfig
from pydex_app.constants import NULL_ADDRESS, RINKEBY_NETWORK_ID, NETWORK_INFO
from pydex_app.db_models import SignedOrder
from pydex_app.utils import to_base_unit_amount, setup_logger, sign_order
from pydex_client.client import PyDexClient

LOGGER = setup_logger("TestLogger")

NETWORK_ID = RINKEBY_NETWORK_ID
EXCHANGE_ADDRESS = NETWORK_INFO[NETWORK_ID]["exchange_id"]


@pytest.fixture(scope="session")
def logger():
    """Logger object with log file and colorful console output"""
    return LOGGER


@pytest.fixture(scope="session")
def asset_infos():
    """A convenience object for holding all asset info needed for testing.
    Ideally, need to enhance this later to dynamically pull this information
    from the configured network.
    """
    class AssetInfos:
        """Convenience class holding asset info"""
        VETH_TOKEN = "0xc4abc01578139e2105d9c9eba0b0aa6f6a60d082"
        VETH_ASSET_DATA = "0xf47261b0000000000000000000000000c4abc01578139e2105d9c9eba0b0aa6f6a60d082"
        LONG_TOKEN = "0x358b48569a4a4ef6310c1f1d8e50be9d068a50c6"
        LONG_ASSET_DATA = "0xf47261b0000000000000000000000000358b48569a4a4ef6310c1f1d8e50be9d068a50c6"
        SHORT_TOKEN = "0x4a1f5f67c1cf90f176496aa548382c78921ae9f1"
        SHORT_ASSET_DATA = "0xf47261b00000000000000000000000004a1f5f67c1cf90f176496aa548382c78921ae9f1"

        FULL_SET_ASSET_DATA = {
            "LONG": LONG_ASSET_DATA,
            "SHORT": SHORT_ASSET_DATA,
        }

    return AssetInfos


@pytest.fixture(scope="session")
def private_key():
    """Private key from PRIVATE_KEY env var"""
    _private_key = os.environ.get("PRIVATE_KEY")
    assert _private_key, "Please make sure a test PRIVATE_KEY env var is set"
    return binascii.a2b_hex(_private_key)


@pytest.fixture(scope="session")
def web3_rpc_url():
    """Web3 RPC URL from WEB3_RPC_URL env var"""
    _web3_rpc_url = os.environ.get("WEB3_RPC_URL")
    assert _web3_rpc_url, "Please make sure a WEB3_RPC_URL is set"
    return _web3_rpc_url


@pytest.fixture(scope="session")
def web3_instance(web3_rpc_url):  # pylint: disable=redefined-outer-name
    """A web3 instance configured with the web3_rpc_url"""
    web3_provider = HTTPProvider(web3_rpc_url)
    return Web3(web3_provider)


@pytest.fixture(scope="session")
def my_account(web3_instance, private_key):  # pylint: disable=redefined-outer-name
    """Account associated with PRIVATE_KEY"""
    return web3_instance.eth.account.privateKeyToAccount(private_key)


@pytest.fixture(scope="session")
def my_address(my_account):  # pylint: disable=redefined-outer-name
    """Address of my_account as a string"""
    return my_account.address.lower()


@pytest.fixture(scope="session")
def test_app():
    """PyDEX flask app instance with fresh database"""
    temp_db_path = os.path.join(
        os.getcwd(),
        "{}_pydex.db".format(tempfile.mktemp(dir=".tmp")))
    # make sure base_dir is the full dir and file_name is just the filename
    base_dir = os.path.dirname(temp_db_path)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    LOGGER.info("temp_db_path: %s", temp_db_path)

    class PydexTestConfig(PydexBaseConfig):  # pylint: disable=too-few-public-methods
        """Test Config"""
        TESTING = False
        SQLALCHEMY_DATABASE_URI = "sqlite:///{}".format(temp_db_path)

    app = create_app(PydexTestConfig)

    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()
    LOGGER.info("Deleting temp_pdb=%s", temp_db_path)
    os.unlink(temp_db_path)


@pytest.fixture(scope="session")
def test_client(test_app):  # pylint: disable=redefined-outer-name
    """Test client associate with test app"""
    return test_app.test_client()


@pytest.fixture(scope="session")
def pydex_client(web3_rpc_url, private_key):  # pylint: disable=redefined-outer-name
    """An instance of the pyDexClient object configured with the private key"""
    return PyDexClient(
        network_id=NETWORK_ID,
        web3_rpc_url=web3_rpc_url,
        private_key=private_key
    )


@pytest.fixture(scope="session")
def make_veth_signed_order(
    asset_infos,  # pylint: disable=redefined-outer-name
    web3_instance,  # pylint: disable=redefined-outer-name
    private_key,  # pylint: disable=redefined-outer-name
    my_address,  # pylint: disable=redefined-outer-name
):
    """Create a new instance of a signed order"""
    def _make_veth_signed_order(  # pylint: disable=too-many-locals
        asset_type,
        qty,
        price,
        side,
        maker_address=my_address,  # pylint: disable=redefined-outer-name
        expiration_time_secs=600,
        maker_fee="0",
        taker_fee="0",
        salt=None,
        taker_address=NULL_ADDRESS,
        fee_recipient_address=NULL_ADDRESS,
        sender_address=NULL_ADDRESS,
        exchange_address=EXCHANGE_ADDRESS,
        web3_instance=web3_instance,  # pylint: disable=redefined-outer-name
        private_key=private_key,  # pylint: disable=redefined-outer-name

    ):
        """ Convenience function for making valid orders to buy or sell
        SHORT or LONG assets against VETH.

        Keyword arguments:
        asset_type -- str from {'LONG', 'SHORT'} to index into `full_asset_set_data`
        qty -- how much of the ticker asset you want to buy against VETH
        price -- Always in units of LONG or SHORT asset per VETH
        side -- str from {'BUY', 'SELL'}
        maker_address -- your address (defaults to MY_ADDRESS)
        """
        asset_data = asset_infos.FULL_SET_ASSET_DATA[asset_type]
        if side == 'BUY':
            maker_asset_data = asset_infos.VETH_ASSET_DATA
            taker_asset_data = asset_data
            maker_amount = to_base_unit_amount(qty * price)
            taker_amount = to_base_unit_amount(qty)
        elif side == 'SELL':
            maker_asset_data = asset_data
            taker_asset_data = asset_infos.VETH_ASSET_DATA
            maker_amount = to_base_unit_amount(qty)
            taker_amount = to_base_unit_amount(qty * price)
        else:
            raise Exception("side must be one of {'BUY', 'SELL'}")

        if not salt:
            salt = "1234567890"
        if not isinstance(maker_fee, str):
            maker_fee = to_base_unit_amount(maker_fee)
        if not isinstance(taker_fee, str):
            taker_fee = to_base_unit_amount(taker_fee)
        expiration_time_secs = int(time.time() + expiration_time_secs)

        order = SignedOrder()
        order.maker_address = maker_address
        order.taker_address = taker_address
        order.fee_recipient_address = fee_recipient_address
        order.sender_address = sender_address
        order.maker_asset_amount = maker_amount
        order.taker_asset_amount = taker_amount
        order.maker_fee = "{:.0f}".format(Decimal(maker_fee))
        order.taker_fee = "{:.0f}".format(Decimal(taker_fee))
        order.expiration_time_secs = expiration_time_secs
        order.salt = salt
        order.maker_asset_data = maker_asset_data
        order.taker_asset_data = taker_asset_data
        order.exchange_address = exchange_address
        assert_valid(order.update().to_json(), "/orderSchema")
        order.signature = sign_order(order.hash, web3_instance, private_key)
        assert_valid(order.to_json(), "/signedOrderSchema")
        return order

    return _make_veth_signed_order
