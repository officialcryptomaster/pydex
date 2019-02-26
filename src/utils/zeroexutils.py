"""
0x Web3 Utilities

author: officialcryptomaster@gmail.com
"""
from enum import Enum
from eth_utils import keccak
from hexbytes import HexBytes
from zero_ex.contract_artifacts import abi_by_name
from zero_ex.contract_addresses import NetworkId, NETWORK_TO_ADDRESSES
from utils.web3utils import Web3Client

EIP191_HEADER = b"\x19\x01"
ERC20_PROXY_ID = '0xf47261b0'
ERC721_PROXY_ID = '0x02571792'


EIP712_DOMAIN_SEPARATOR_SCHEMA_HASH = keccak(
    b"EIP712Domain(string name,string version,address verifyingContract)"
)


EIP712_ORDER_SCHEMA_HASH = keccak(
    b"Order("
    + b"address makerAddress,"
    + b"address takerAddress,"
    + b"address feeRecipientAddress,"
    + b"address senderAddress,"
    + b"uint256 makerAssetAmount,"
    + b"uint256 takerAssetAmount,"
    + b"uint256 makerFee,"
    + b"uint256 takerFee,"
    + b"uint256 expirationTimeSeconds,"
    + b"uint256 salt,"
    + b"bytes makerAssetData,"
    + b"bytes takerAssetData"
    + b")"
)


EIP712_DOMAIN_STRUCT_HEADER = (
    EIP712_DOMAIN_SEPARATOR_SCHEMA_HASH
    + keccak(b"0x Protocol")
    + keccak(b"2")
)


class ZrxOrderStatus(Enum):
    """OrderStatus codes used by 0x contracts"""
    INVALID = 0  # Default value
    INVALID_MAKER_ASSET_AMOUNT = 1  # Order does not have a valid maker asset amount
    INVALID_TAKER_ASSET_AMOUNT = 2  # Order does not have a valid taker asset amount
    FILLABLE = 3  # Order is fillable
    EXPIRED = 4  # Order has already expired
    FULLY_FILLED = 5  # Order is fully filled
    CANCELLED = 6  # Order has been cancelled


class ZrxOrderInfo:  # pylint: disable=too-few-public-methods
    """A Web3-compatible representation of the Exchange.OrderInfo struct"""

    __name__ = "OrderInfo"

    def __init__(
        self,
        order_status,
        order_hash,
        order_taker_asset_filled_amount
    ):
        """Create an instance of Exchange.OrderInfo struct

        Keyword arguments:
        order_status -- ZrxOrderStatus enum indicating order status
        order_hash -- hexbyte of order hash
        order_taker_assert_filled_amount -- integer order taker asset filled amount
        """
        self.order_status = ZrxOrderStatus(order_status)
        self.order_hash = HexBytes(order_hash)
        self.order_taker_asset_filled_amount = int(order_taker_asset_filled_amount)

    def __str__(self):
        return (
            f"[{self.__name__}]({self.order_status}, {self.order_hash.hex()}"
            f", filled_amount={self.order_taker_asset_filled_amount})")

    __repr__ = __str__


class ZeroExWeb3Client(Web3Client):
    """Client for interacting with 0x """

    __name__ = "ZrxWeb3Client"

    def __init__(
        self,
        network_id,
        web3_rpc_url,
        private_key=None,
    ):
        """Create an instance of the Web3Client with a private key

        Keyword arguments:
        network_id -- numerable id of networkId convertible to `constants.NetworkId`
        web3_rpc_url -- string of the URL of the Web3 service
        private_key -- hex bytes or hex string of private key for signing transactions
            (must be convertible to `HexBytes`) (default: None)
        """
        super(ZeroExWeb3Client, self).__init__(
            network_id=network_id,
            web3_rpc_url=web3_rpc_url,
            private_key=private_key,
        )
        self._contract_addressess = NETWORK_TO_ADDRESSES[NetworkId(self._network_id)]
        self._zrx_exchange = None

    @property
    def exchange_address_checksumed(self):
        """Return a checksum version of the address of the  0x exchange contract"""
        return self.get_checksum_address(self._contract_addressess.exchange)

    @property
    def zrx_exchange(self):
        """Returns an instance of the 0x Exchange contract"""
        if self._zrx_exchange is None:
            self._zrx_exchange = self._web3_eth.contract(
                address=self.exchange_address_checksumed,
                abi=abi_by_name("exchange"))
        return self._zrx_exchange

    def sign_hash_0x_compat(self, hash_hex):
        """Returns a 0x-compatible signature from signing a hash_hex with eth-sign

        Keyword argument:
        hash_hex -- hex bytes or hex str of a hash to sign
            (must be convertile to `HexBytes`)
        """
        ec_signature = self.sign_hash(hash_hex)
        return self.get_0x_signature_from_ec_signature(ec_signature=ec_signature)

    @staticmethod
    def get_0x_signature_from_ec_signature(ec_signature):
        """Returns a hex string 0x-compatible signature from an eth-sign ec_signature

        0x signature is a hexstr made from the concatenation of the hexstr of the "v",
        r", and "s" parameters of an ec_signature and ending with constant "03" to
        indicate "eth-sign" was used.
        The "r" and "s" parts of the signature need to each represent 32 bytes
        and so will be righ-justified with "0" padding on the left (i.e. "r" and "s"
        will be strings of 64 hex characters each, which means no leading "0x")

        Keyword argument:
        ec_singature -- A dict containing "r", "s" and "v" parameters of an elliptic
            curve signature as integers
        """
        v = hex(ec_signature["v"])  # pylint: disable=invalid-name
        r = HexBytes(ec_signature["r"]).rjust(32, b"\0").hex()  # pylint: disable=invalid-name
        s = HexBytes(ec_signature["s"]).rjust(32, b"\0").hex()  # pylint: disable=invalid-name
        # append "03" to specify signature type of eth-sign
        return v + r + s + "03"

    @classmethod
    def get_order_hash(cls, order):
        """Returns hex string hash of 0x order

        Keyword argument:
        order -- dict representing a 0x order
        """
        eip712_domain_struct_hash = keccak(
            EIP712_DOMAIN_STRUCT_HEADER
            + HexBytes(order["exchangeAddress"]).rjust(32, b"\0")
        )

        eip712_order_struct_hash = keccak(
            EIP712_ORDER_SCHEMA_HASH
            + HexBytes(order["makerAddress"]).rjust(32, b"\0")
            + HexBytes(order["takerAddress"]).rjust(32, b"\0")
            + HexBytes(order["feeRecipientAddress"]).rjust(32, b"\0")
            + HexBytes(order["senderAddress"]).rjust(32, b"\0")
            + int(order["makerAssetAmount"]).to_bytes(32, byteorder="big")
            + int(order["takerAssetAmount"]).to_bytes(32, byteorder="big")
            + int(order["makerFee"]).to_bytes(32, byteorder="big")
            + int(order["takerFee"]).to_bytes(32, byteorder="big")
            + int(order["expirationTimeSeconds"]).to_bytes(32, byteorder="big")
            + int(order["salt"]).to_bytes(32, byteorder="big")
            + keccak(HexBytes(order["makerAssetData"]))
            + keccak(HexBytes(order["takerAssetData"]))
        )

        return "0x" + keccak(
            EIP191_HEADER
            + eip712_domain_struct_hash
            + eip712_order_struct_hash
        ).hex()

    @classmethod
    def get_order_for_web3(cls, order):
        """Returns a dict of copy of the order with"""
        _order = {}
        _order["makerAddress"] = cls.get_checksum_address(order["makerAddress"])
        _order["takerAddress"] = cls.get_checksum_address(order["takerAddress"])
        _order["feeRecipientAddress"] = cls.get_checksum_address(order["feeRecipientAddress"])
        _order["senderAddress"] = cls.get_checksum_address(order["senderAddress"])
        _order["exchangeAddress"] = cls.get_checksum_address(order["exchangeAddress"])
        _order["makerAssetAmount"] = int(order["makerAssetAmount"])
        _order["takerAssetAmount"] = int(order["takerAssetAmount"])
        _order["makerFee"] = int(order["makerFee"])
        _order["takerFee"] = int(order["takerFee"])
        _order["expirationTimeSeconds"] = int(order["expirationTimeSeconds"])
        _order["salt"] = int(order["salt"])
        _order["makerAssetData"] = HexBytes(order["makerAssetData"])
        _order["takerAssetData"] = HexBytes(order["takerAssetData"])
        return _order

    def fill_order(
        self,
        signed_order,
        taker_fill_amount,
        base_unit_decimals=18,
    ):
        """Call the fillOrder function of the 0x Exchange contract

        Keyword arguments:
        order -- dict representing a 0x order with signature on it
        taker_fill_amount -- integer amount of taker Asset (will be converted
            to base units by multiplying by 10**base_unit_decimals)
        """
        signature = HexBytes(signed_order["signature"])
        order = self.get_order_for_web3(signed_order)
        taker_fill_amount = int(taker_fill_amount * 10**base_unit_decimals)
        func = self.zrx_exchange.functions.fillOrder(
            order,
            taker_fill_amount,
            signature
        )
        return self._build_and_send_tx(func)

    def _build_and_send_tx(self, func, gas=150000):
        """Build and send a transaction and return its receipt hash

        Keyword arguments:
        func -- function object constructed with the right paramters
        gas_limit -- integer limit gas to spend in base units (WEI) (default: 150000)
        """
        tx_params = self._get_tx_params(gas=gas)
        transaction = func.buildTransaction(tx_params)
        signed_tx = self._web3_eth.account.signTransaction(
            transaction, private_key=self._private_key)
        return self._web3_eth.sendRawTransaction(signed_tx.rawTransaction)

    def _get_tx_params(self, gas=150000):
        """Get dict of generic transaction parameters

        Keyword argument:
        gas -- integer amount of gas to spend in transaction (default: 150000)
        """
        return {
            "from": self.account_address_checksumed,
            "value": 0,  # we don't ever want to transfer any ETH
            "gas": gas,
            "nonce": self._web3_eth.getTransactionCount(
                self.account_address_checksumed)
        }
