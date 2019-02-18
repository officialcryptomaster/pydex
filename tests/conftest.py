"""
Fixtures for pytest

author: originalcryptomaster@gmail.com
"""

import os
import random
import tempfile

from decimal import Decimal
import time
import pytest

from zero_ex.json_schemas import assert_valid
from zero_ex.contract_addresses import NETWORK_TO_ADDRESSES, NetworkId

from pydex_app import create_app
from pydex_app.config import PydexBaseConfig
from pydex_app.constants import NULL_ADDRESS
from pydex_app.db_models import SignedOrder
from pydex_client.client import PyDexClient
from utils.logutils import setup_logger
from utils.web3utils import to_base_unit_amount

LOGGER = setup_logger("TestLogger")


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
    class AssetInfos:  # pylint: disable=too-few-public-methods
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
def network_id():
    """Integer network ID hard-coded to 50 for Ganache"""
    return NetworkId.GANACHE.value


@pytest.fixture(scope="session")
def exchange_address(network_id):  # pylint: disable=redefined-outer-name
    """String address of the 0x Exchange contract on provided network_id"""
    return NETWORK_TO_ADDRESSES[NetworkId(int(network_id))].exchange


@pytest.fixture(scope="session")
def web3_rpc_url():
    """String url of Web3 RPC service
    hard-coded to default local Ganache port 8445
    """
    return "http://127.0.0.1:8545"


@pytest.fixture(scope="session")
def private_key():
    """String private key hard-coded as first account on 0x ganache snapshot
    mnemonic = "concert load couple harbor equip island argue ramp clarify fence smart topic"
    private_key = "f2f48ee19680706196e2e339e5da3491186e0c4c5030670656b0e0164837257d"
    """
    return "f2f48ee19680706196e2e339e5da3491186e0c4c5030670656b0e0164837257d"


@pytest.fixture(scope="session")
def test_app(network_id):  # pylint: disable=redefined-outer-name
    """PyDex flask app instance with fresh database"""
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
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///{}".format(temp_db_path)
        PYDEX_NETWORK_ID = network_id

    app = create_app(PydexTestConfig)

    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()
    LOGGER.info("Deleting temp_pdb=%s", temp_db_path)
    os.unlink(temp_db_path)


@pytest.fixture(scope="session")
def test_client(test_app):  # pylint: disable=redefined-outer-name
    """Test client instance associate with test app"""
    return test_app.test_client()


@pytest.fixture(scope="session")
def pydex_client(network_id, web3_rpc_url, private_key):  # pylint: disable=redefined-outer-name
    """pyDexClient instance configured with the private key"""
    return PyDexClient(
        network_id=network_id,
        web3_rpc_url=web3_rpc_url,
        private_key=private_key
    )


@pytest.fixture(scope="session")
def make_veth_signed_order(
    asset_infos,  # pylint: disable=redefined-outer-name
    pydex_client,  # pylint: disable=redefined-outer-name
    exchange_address,  # pylint: disable=redefined-outer-name
):
    """Convenience function for creating a new instance of a signed order"""
    def _make_veth_signed_order(  # pylint: disable=too-many-locals
        asset_type,
        qty,
        price,
        side,
        maker_address=pydex_client.account_address,
        expiration_time_secs=600,
        maker_fee="0",
        taker_fee="0",
        salt="1234567890",
        taker_address=NULL_ADDRESS,
        fee_recipient_address=NULL_ADDRESS,
        sender_address=NULL_ADDRESS,
        exchange_address=exchange_address,  # pylint: disable=redefined-outer-name
        pydex_client=pydex_client,  # pylint: disable=redefined-outer-name
    ):
        """Convenience function for making valid orders to buy or sell
        SHORT or LONG assets against VETH.

        Keyword arguments:
        asset_type - - str from {'LONG', 'SHORT'} to index into `full_asset_set_data`
        qty - - how much of the ticker asset you want to buy against VETH
        price - - Always in units of LONG or SHORT asset per VETH
        side - - str from {'BUY', 'SELL'}
        maker_address - - your address(defaults to MY_ADDRESS)
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

        if salt is None:
            salt = "{:.0f}".format(Decimal(random.uniform(0, 9223372036854775807)))
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
        # sign the hash
        order.signature = pydex_client.sign_hash_0x_compat(order.update().hash)
        # make sure the signed_order is valid
        assert_valid(order.to_json(), "/signedOrderSchema")
        return order

    return _make_veth_signed_order
