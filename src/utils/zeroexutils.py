"""
0x Web3 Utilities

author: officialcryptomaster@gmail.com
"""
from decimal import Decimal
from enum import Enum
from eth_utils import keccak
from hexbytes import HexBytes
from zero_ex.json_schemas import assert_valid
from zero_ex.contract_artifacts import abi_by_name
from zero_ex.contract_addresses import NetworkId, NETWORK_TO_ADDRESSES
from utils.miscutils import try_, assert_like_integer, now_epoch_msecs, \
    epoch_secs_to_local_time_str, epoch_msecs_to_local_time_str
from utils.web3utils import Web3Client, get_clean_address_or_throw, NULL_ADDRESS

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


class ZxOrderStatus(Enum):
    """OrderStatus codes used by 0x contracts"""
    INVALID = 0  # Default value
    INVALID_MAKER_ASSET_AMOUNT = 1  # Order does not have a valid maker asset amount
    INVALID_TAKER_ASSET_AMOUNT = 2  # Order does not have a valid taker asset amount
    FILLABLE = 3  # Order is fillable
    EXPIRED = 4  # Order has already expired
    FULLY_FILLED = 5  # Order is fully filled
    CANCELLED = 6  # Order has been cancelled


class ZxOrderInfo:  # pylint: disable=too-few-public-methods
    """A Web3-compatible representation of the Exchange.OrderInfo struct"""

    __name__ = "OrderInfo"

    def __init__(
        self,
        zx_order_status,
        order_hash,
        order_taker_asset_filled_amount
    ):
        """Create an instance of Exchange.OrderInfo struct

        Keyword arguments:
        zx_order_status -- ZxOrderStatus enum indicating order status
        order_hash -- hexbyte of order hash
        order_taker_assert_filled_amount -- integer order taker asset filled amount
        """
        self.zx_order_status = ZxOrderStatus(zx_order_status)
        self.order_hash = HexBytes(order_hash)
        self.order_taker_asset_filled_amount = int(order_taker_asset_filled_amount)

    def __str__(self):
        return (
            f"[{self.__name__}]"
            f"({try_(ZxOrderStatus, self.zx_order_status)}"
            f", {self.order_hash.hex()}"
            f", filled_amount={self.order_taker_asset_filled_amount})")

    __repr__ = __str__


class ZxSignedOrder:  # pylint: disable=too-many-public-methods
    """ZxSignedOrder

    This object will keep the database-friendly formats in member variables
    starting with underscore, and provide property setter and getters for
    getting the values in useful formats
    """

    __name__ = "ZxSignedOrder"

    def __init__(self, **kwargs):
        # initialize all serialized (i.e. DB storable) columns as members
        # ending with underscore.
        self.hash_ = None
        self.maker_address_ = None
        self.taker_address_ = None
        self.fee_recipient_address_ = None
        self.sender_address_ = None
        self.exchange_address_ = None
        self.maker_asset_amount_ = None
        self.taker_asset_amount_ = None
        self.maker_fee_ = None
        self.taker_fee_ = None
        self.salt_ = None
        self.expiration_time_secs_ = None
        self.maker_asset_data_ = None
        self.taker_asset_data_ = None
        self.signature_ = None
        # book-keeping fields
        self.created_at_msecs_ = None
        self.bid_price_ = None
        self.ask_price_ = None
        self.sort_price_ = None

        # assign keyword args and default values
        self._created_at_msecs_ = kwargs.get("created_at_msecs") or now_epoch_msecs()
        self.hash_ = kwargs.get("hash") or None
        self.maker_address = kwargs.get("maker_address") or NULL_ADDRESS
        self.taker_address = kwargs.get("taker_address") or NULL_ADDRESS
        self.fee_recipient_address = kwargs.get("fee_recipient_address") or NULL_ADDRESS
        self.sender_address = kwargs.get("sender_address") or NULL_ADDRESS
        self.exchange_address = kwargs.get("exchange_address") or NULL_ADDRESS
        self.maker_asset_amount = kwargs.get("maker_asset_amount") or "0"
        self.taker_asset_amount = kwargs.get("taker_asset_amount") or "0"
        self.taker_fee = kwargs.get("taker_fee") or "0"
        self.maker_fee = kwargs.get("maker_fee") or "0"
        self.salt = kwargs.get("salt") or "0"
        # default expiry to one minute after creation
        self.expiration_time_secs = kwargs.get("expiration_time_secs") \
            or self._created_at_msecs_ / 1000. + 60
        self.maker_asset_data = kwargs.get("maker_asset_data") or None
        self.taker_asset_data = kwargs.get("taker_asset_data") or None
        self.signature_ = kwargs.get("signature") or None

    def __str__(self):
        return (
            f"[{self.__name__}]"
            f"(hash={self.hash}"
            f" | maker_asset_amount={self.maker_asset_amount}"
            f" | taker_asset_amount={self.taker_asset_amount}"
            f" | maker_asset_data={self.maker_asset_data}"
            f" | taker_asset_data={self.taker_asset_data}"
            f" | maker_address={self.maker_address}"
            f" | taker_address={self.taker_address}"
            f" | signature={self.signature}"
            f" | expires={self.expiration_time}"
            ")"
        )

    __repr__ = __str__

    @property
    def hash(self):
        """Get hash of the order with lazy evaluation"""
        if self.hash_ is None:
            try_(self.update_hash)
        return self.hash_

    @property
    def maker_address(self):
        """Get maker address as hex string"""
        return self.maker_address_

    @maker_address.setter
    def maker_address(self, value):
        """Set maker address with validation

        Keyword argument:
        value -- hex string of maker address
        """
        self.maker_address_ = None if value is None else get_clean_address_or_throw(value)

    @property
    def taker_address(self):
        """Get taker address as hex string"""
        return self.taker_address_

    @taker_address.setter
    def taker_address(self, value):
        """Set taker address with validation

        Keyword argument:
        value -- hex string of taker address
        """
        self.taker_address_ = None if value is None else get_clean_address_or_throw(value)

    @property
    def fee_recipient_address(self):
        """Get fee recipient address as hex string"""
        return self.fee_recipient_address_

    @fee_recipient_address.setter
    def fee_recipient_address(self, value):
        """Set fee recipient address with validation

        Keyword argument:
        value -- hex string of fee recipient address
        """
        self.fee_recipient_address_ = None if value is None else get_clean_address_or_throw(value)

    @property
    def sender_address(self):
        """Get sender address as hex string"""
        return self.sender_address_

    @sender_address.setter
    def sender_address(self, value):
        """Set sender address with validation

        Keyword argument:
        value -- hex string of sender address
        """
        self.sender_address_ = None if value is None else get_clean_address_or_throw(value)

    @property
    def exchange_address(self):
        """Get exchange address as hex string"""
        return self.exchange_address_

    @exchange_address.setter
    def exchange_address(self, value):
        """Set exchange address with validation

        Keyword argument:
        value -- hex string of exchange contract address
        """
        self.exchange_address_ = None if value is None else get_clean_address_or_throw(value)

    @property
    def maker_asset_amount(self):
        """Get maker asset amount as integer in base units"""
        return int(self.maker_asset_amount_)

    @maker_asset_amount.setter
    def maker_asset_amount(self, value):
        """Set maker asset amount in base units

        Keyword argument:
        value -- integer-like maker asset amount in base units
        """
        assert_like_integer(value)
        self.maker_asset_amount_ = "{:.0f}".format(Decimal(value))
        self.update_bid_price()
        self.update_ask_price()

    @property
    def taker_asset_amount(self):
        """Get taker asset amount as integer in base units"""
        return int(self.taker_asset_amount_)

    @taker_asset_amount.setter
    def taker_asset_amount(self, value):
        """Set taker asset amount in base units

        Keyword argument:
        value -- integer-like taker asset amount in base units
        """
        assert_like_integer(value)
        self.taker_asset_amount_ = "{:.0f}".format(Decimal(value))
        self.update_bid_price()
        self.update_ask_price()

    @property
    def maker_fee(self):
        """Get maker fee as integer in base units"""
        return int(self.maker_fee_)

    @maker_fee.setter
    def maker_fee(self, value):
        """Set maker fee in base units

        Keyword argument:
        value -- integer-like maker fee in base units
        """
        assert_like_integer(value)
        self.maker_fee_ = "{:.0f}".format(Decimal(value))

    @property
    def taker_fee(self):
        """Get taker fee as integer in base units"""
        return int(self.taker_fee_)

    @taker_fee.setter
    def taker_fee(self, value):
        """Set taker fee in base units

        Keyword argument:
        value -- integer-like taker fee in base units
        """
        assert_like_integer(value)
        self.taker_fee_ = "{:.0f}".format(Decimal(value))

    @property
    def salt(self):
        """Get salt as integer"""
        return int(self.salt_)

    @salt.setter
    def salt(self, value):
        """Set salt from integer-like

        Keyword argument:
        value -- integer-like salt value
        """
        assert_like_integer(value)
        self.salt_ = "{:.0f}".format(Decimal(value))

    @property
    def expiration_time(self):
        """Get expiration as naive datetime"""
        return try_(epoch_secs_to_local_time_str, self.expiration_time_secs_)

    @property
    def expiration_time_secs(self):
        """Get expiration time in seconds since epoch"""
        return self.expiration_time_secs_

    @expiration_time_secs.setter
    def expiration_time_secs(self, value):
        """Set expiration time secs from numeric-like

        Keyword argument:
        value -- numeric-like expiration time in seconds since epoch
        """
        self.expiration_time_secs_ = int("{:.0f}".format(Decimal(value)))

    @property
    def maker_asset_data(self):
        """Get asset data as HexBytes"""
        return self.maker_asset_data_

    @maker_asset_data.setter
    def maker_asset_data(self, value):
        """Set maker asset data

        Keyword argument:
        value -- hexbytes-like maker asset data
        """
        self.maker_asset_data_ = HexBytes(value).hex() if value is not None else None

    @property
    def taker_asset_data(self):
        """Get asset data as hex string"""
        return self.taker_asset_data_

    @taker_asset_data.setter
    def taker_asset_data(self, value):
        """Set taker asset data

        Keyword argument:
        value -- hexbytes-like taker asset data
        """
        self.taker_asset_data_ = HexBytes(value).hex() if value is not None else None

    @property
    def signature(self):
        """Return the signaure of the SignedOrder"""
        return self.signature_

    @signature.setter
    def signature(self, value):
        """Set the signature"""
        self.signature_ = HexBytes(value).hex() if value is not None else None

    @property
    def created_at_msecs(self):
        """Get creation time in milliseconds since epoch"""
        return self.created_at_msecs_

    @property
    def created_at(self):
        """Get creation time timestamp as naive DateTime"""
        return try_(epoch_msecs_to_local_time_str, self.created_at_msecs_)

    @property
    def bid_price(self):
        """Get bid price as a Decimal"""
        return try_(Decimal, self.bid_price_, Decimal(0))

    @property
    def ask_price(self):
        """Get ask price as a Decimal"""
        return try_(Decimal, self.ask_price_, Decimal("9" * 32))

    @property
    def sort_price(self):
        """Get sort price
        This is useful for full set order which result in a mix of bids and asks
        (hint: make use of `set_bid_price_as_sort_price` and its equivalent
        `set_bid_price_as_sort_price`)
        """
        return Decimal(self.sort_price_)

    def update_hash(self):
        """Update the hash of the order and return the order for chaining"""
        self.hash_ = self.get_order_hash(self.to_json())
        return self

    def update(self):
        """Call all update functions for order and return order for chaining"""
        self.update_hash()
        return self

    def update_bid_price(self):
        """Bid price is price of taker asset per unit of maker asset
        (i.e. price of taker asset which maker is bidding to buy)
        """
        try:
            self.bid_price_ = "{:032.18f}".format(
                Decimal(self.taker_asset_amount) / Decimal(self.maker_asset_amount))
        except:  # noqa E722 pylint: disable=bare-except
            self.bid_price_ = "0" * 32
        return self

    def update_ask_price(self):
        """Ask price is price of maker asset per unit of taker asset
        (i.e. price of maker asset the maker is asking to sell)
        """
        try:
            self.ask_price_ = "{:032.18f}".format(
                Decimal(self.maker_asset_amount) / Decimal(self.taker_asset_amount))
        except:  # noqa E722 pylint: disable=bare-except
            self.ask_price_ = "9" * 32
        return self

    def set_bid_as_sort_price(self):
        """Set the self.sort_price_ field to be the self.bid_price_
        This can be useful for sorting full set orders
        """
        self.sort_price_ = self.bid_price_
        return self

    def set_ask_as_sort_price(self):
        """Set the self._sort_price field to be the self.ask_price_
        This can be useful for sorting full set orders
        """
        self.sort_price_ = self.ask_price_
        return self

    def to_json(
        self,
        include_hash=False,
        include_signature=True,
    ):
        """Get a json representation of the SignedOrder"""
        order = {
            "makerAddress": self.maker_address_,
            "takerAddress": self.taker_address_,
            "feeRecipientAddress": self.fee_recipient_address_,
            "senderAddress": self.sender_address_,
            "exchangeAddress": self.exchange_address_,
            "makerAssetAmount": self.maker_asset_amount_,
            "takerAssetAmount": self.taker_asset_amount_,
            "makerFee": self.maker_fee_,
            "takerFee": self.taker_fee_,
            "salt": self.salt_,
            "expirationTimeSeconds": self.expiration_time_secs_,
            "makerAssetData": self.maker_asset_data_,
            "takerAssetData": self.taker_asset_data_,
        }
        if include_hash:
            order["hash"] = self.hash
        if include_signature:
            order["signature"] = self.signature
        return order

    @classmethod
    def get_order_hash(cls, order_json):
        """Returns hex string hash of 0x order

        Keyword argument:
        order_json -- a dict conforming to "/signedOrderSchema" or "/orderSchema"
            (dependign on whether `include_signature` is set to True or False)
            schemas can be found at:
            <https://github.com/0xProject/0x-monorepo/tree/development/packages/json-schemas/schemas>
        """
        order = order_json
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
    def from_json(
        cls,
        order_json,
        check_validity=False,
        include_signature=True,
    ):
        """Given a json representation of a signed order, return a SignedOrder object

        Keyword arguments:
        order_json -- a dict conforming to "/signedOrderSchema" or "/orderSchema"
            (dependign on whether `include_signature` is set to True or False)
            schemas can be found at:
            <https://github.com/0xProject/0x-monorepo/tree/development/packages/json-schemas/schemas>
        check_validity -- whether we should do an explicit check to make sure the
            passed in dict adheres to the required schema (default: True)
        include_signature -- whether the object is expected to have the signature on it
            or not. This will affect whether "/signedOrderSchema" or "/orderSchema" is
            used for validation (default: True)
        """
        order = cls()
        if check_validity:
            if include_signature:
                assert_valid(order_json, "/signedOrderSchema")
            else:
                assert_valid(order_json, "/orderSchema")
        order.maker_address = order_json["makerAddress"]
        order.taker_address = order_json["takerAddress"]
        order.maker_fee = order_json["makerFee"]
        order.taker_fee = order_json["takerFee"]
        order.sender_address = order_json["senderAddress"]
        order.maker_asset_amount = order_json["makerAssetAmount"]
        order.taker_asset_amount = order_json["takerAssetAmount"]
        order.maker_asset_data = order_json["makerAssetData"]
        order.taker_asset_data = order_json["takerAssetData"]
        order.salt = order_json["salt"]
        order.exchange_address = order_json["exchangeAddress"]
        order.fee_recipient_address = order_json["feeRecipientAddress"]
        order.expiration_time_secs = order_json["expirationTimeSeconds"]
        if include_signature:
            order.signature = order_json["signature"]
        order.update()
        return order


class ZxWeb3Client(Web3Client):
    """Client for interacting with 0x """

    __name__ = "ZxWeb3Client"

    def __init__(
        self,
        network_id,
        web3_rpc_url,
        private_key=None,
    ):
        """Create an instance of the ZeroExWeb3Client

        Keyword arguments:
        network_id -- numerable id of networkId convertible to `constants.NetworkId`
        web3_rpc_url -- string of the URL of the Web3 service
        private_key -- hex bytes or hex string of private key for signing transactions
            (must be convertible to `HexBytes`) (default: None)
        """
        super(ZxWeb3Client, self).__init__(
            network_id=network_id,
            web3_rpc_url=web3_rpc_url,
            private_key=private_key,
        )
        self._contract_addressess = NETWORK_TO_ADDRESSES[NetworkId(self._network_id)]
        self._zx_exchange = None

    @property
    def exchange_address_checksumed(self):
        """Return a checksum version of the address of the  0x exchange contract"""
        return self.get_checksum_address(self._contract_addressess.exchange)

    @property
    def zx_exchange(self):
        """Returns an instance of the 0x Exchange contract"""
        if self._zx_exchange is None:
            self._zx_exchange = self._web3_eth.contract(
                address=self.exchange_address_checksumed,
                abi=abi_by_name("exchange"))
        return self._zx_exchange

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
    def get_order_for_web3(cls, order_json):
        """Get a copy of the order json converted to web3 consumption

        Keyword argument:
        order_json -- a dict conforming to "/orderSchema" defined in:
            <https://github.com/0xProject/0x-monorepo/tree/development/packages/json-schemas/schemas>
        """
        order = order_json
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

    def cancel_order(
        self,
        order,
    ):
        """Call the cancelOrder function of the 0x Exchange contract

        Keyword arguments:
        order -- dict representing a 0x order
        """
        order_to_cancel = self.get_order_for_web3(order)
        func = self.zx_exchange.functions.cancelOrder(order_to_cancel)
        return self._build_and_send_tx(func)

    def fill_order(
        self,
        signed_order_json,
        taker_fill_amount,
        base_unit_decimals=18,
    ):
        """Call the fillOrder function of the 0x Exchange contract

        Keyword arguments:
        order -- ZxSignedOrder object or a dict representing a 0x order with
            signature on it
        signed_order_json -- a dict conforming to "/signedOrderSchema" defined in:
            <https://github.com/0xProject/0x-monorepo/tree/development/packages/json-schemas/schemas>
        taker_fill_amount -- integer amount of taker Asset (will be converted
            to base units by multiplying by 10**base_unit_decimals)
        """
        signed_order = signed_order_json
        assert_valid(signed_order, "/signedOrderSchema")
        signature = HexBytes(signed_order["signature"])
        signed_order_web3 = self.get_order_for_web3(signed_order)
        taker_fill_amount = int(taker_fill_amount * 10**base_unit_decimals)
        func = self.zx_exchange.functions.fillOrder(
            signed_order_web3,
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
