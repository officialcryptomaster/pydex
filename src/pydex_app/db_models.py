"""
Database models of common objects

author: officialcryptomaster@gmail.com
"""
from decimal import Decimal
from eth_utils import keccak, to_bytes
from zero_ex.json_schemas import assert_valid
from pydex_app.database import PYDEX_DB as db
from pydex_app.constants import NULL_ADDRESS
from pydex_app.constants import ZERO_STR, MAX_INT_STR


eip191_header = b"\x19\x01"  # pylint: disable=invalid-name


eip712_domain_separator_schema_hash = keccak(  # pylint: disable=invalid-name
    b"EIP712Domain(string name,string version,address verifyingContract)"
)


eip712_order_schema_hash = keccak(  # pylint: disable=invalid-name
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


eip712_domain_struct_header = (  # pylint: disable=invalid-name
    eip712_domain_separator_schema_hash
    + keccak(b"0x Protocol")
    + keccak(b"2")
)


class SignedOrder(db.Model):
    """SignedOrder model which provides persistence and convenience
    methods around dealing with 0x SignedOrder type
    """
    # it faster and easier to work with order_utils
    hash = db.Column(db.String(42), unique=True, primary_key=True)  # pylint: disable=no-member
    maker_address = db.Column(db.String(42), nullable=False)  # pylint: disable=no-member
    taker_address = db.Column(db.String(42), default=NULL_ADDRESS)  # pylint: disable=no-member
    maker_fee = db.Column(db.String(32), default="0")  # pylint: disable=no-member
    taker_fee = db.Column(db.String(32), default="0")  # pylint: disable=no-member
    sender_address = db.Column(db.String(42), default=NULL_ADDRESS)  # pylint: disable=no-member
    maker_asset_amount = db.Column(db.String(128), nullable=False)  # pylint: disable=no-member
    taker_asset_amount = db.Column(db.String(128), nullable=False)  # pylint: disable=no-member
    maker_asset_data = db.Column(db.String(128), nullable=False)  # pylint: disable=no-member
    taker_asset_data = db.Column(db.String(128), nullable=False)  # pylint: disable=no-member
    salt = db.Column(db.String(128), nullable=False)  # pylint: disable=no-member
    exchange_address = db.Column(db.String(42), nullable=False)  # pylint: disable=no-member
    fee_recipient_address = db.Column(db.String(42), default=NULL_ADDRESS)  # pylint: disable=no-member
    expiration_time_secs = db.Column(db.Integer, nullable=False)  # pylint: disable=no-member
    signature = db.Column(db.String(256), nullable=False)  # pylint: disable=no-member
    bid_price = db.Column(db.String(128))  # pylint: disable=no-member
    ask_price = db.Column(db.String(128))  # pylint: disable=no-member
    _sort_price = None  # not a DB column

    @property
    def sort_price(self):
        """Get a price for sorting orders
        This is useful for full set order which result in a mix of bids and asks
        (hint: make use of `set_bid_price_as_sort_price` and its equivalent
        `set_bid_price_as_sort_price`)
        """
        return self._sort_price

    def __repr__(self):
        return (
            f"[SignedOrder](hash={self.hash}"
            f" | bid_price={self.bid_price}"
            f" | ask_price={self.ask_price}"
            f" | maker_asset_amount={self.maker_asset_amount}"
            f" | taker_asset_amount={self.taker_asset_amount}"
            f" | maker_asset_data={self.maker_asset_data}"
            f" | taker_asset_data={self.taker_asset_data}"
            f" | maker_address={self.maker_address}"
            f" | taker_address={self.taker_address}"
        )

    __str__ = __repr__

    def to_json(
        self,
        include_hash=False,
        include_signature=True,
    ):
        """Get a json representation of the SignedOrder"""
        order = {
            "makerAddress": self.maker_address,
            "takerAddress": self.taker_address,
            "makerFee": self.maker_fee,
            "takerFee": self.taker_fee,
            "senderAddress": self.sender_address,
            "makerAssetAmount": self.maker_asset_amount,
            "takerAssetAmount": self.taker_asset_amount,
            "makerAssetData": self.maker_asset_data,
            "takerAssetData": self.taker_asset_data,
            "exchangeAddress": self.exchange_address,
            "salt": self.salt,
            "feeRecipientAddress": self.fee_recipient_address,
            "expirationTimeSeconds": self.expiration_time_secs,
        }
        if include_hash:
            if not self.hash:
                self.update_hash()
            order["hash"] = self.hash
        if include_signature:
            order["signature"] = self.signature
        return order

    def update_bid_ask_prices(self):
        """Update the bid and ask prices and return the order for chaining"""
        self.update_bid_price()
        self.update_ask_price()
        return self

    def update_hash(self):
        """Update the hash of the order and return the order for chaining"""
        self.hash = self.get_order_hash_hex(self)
        return self

    def update(self):
        """Ensure any fields that need calculation are updated
        TODO(CM): consider making use of properties to make this more convenient
        """
        self.update_bid_ask_prices()
        self.update_hash()
        return self

    def update_bid_price(self, default_price=ZERO_STR):
        """Bid price is price of taker asset per unit of maker asset
        (i.e. price of taker asset which maker is bidding to buy)
        """
        try:
            self.bid_price = "{:.18f}".format(
                Decimal(self.taker_asset_amount) / Decimal(self.maker_asset_amount))
        except:  # noqa E722 pylint: disable=bare-except
            self.bid_price = default_price
        return self

    def update_ask_price(self, default_price=MAX_INT_STR):
        """Ask price is price of maker asset per unit of taker asset
        (i.e. price of maker asset the maker is asking to sell)
        """
        try:
            self.ask_price = "{:.18f}".format(
                Decimal(self.maker_asset_amount) / Decimal(self.taker_asset_amount))
        except:  # noqa E722 pylint: disable=bare-except
            self.ask_price = default_price
        return self

    def set_bid_as_sort_price(self):
        """Set the self._sort_price field to be the self.bid_price
        This can be useful for sorting full set orders
        """
        self._sort_price = self.bid_price
        return self

    def set_ask_as_sort_price(self):
        """Set the self._sort_price field to be the self.ask_price
        This can be useful for sorting full set orders
        """
        self._sort_price = self.ask_price
        return self

    @classmethod
    def get_order_hash_hex(cls, order):
        """Calculate hash of an order as per 0x specification"""
        def pad_20_bytes_to_32(twenty_bytes: bytes):
            return bytes(12) + twenty_bytes

        def int_to_32_big_endian_bytes(i: int):
            return i.to_bytes(32, byteorder="big")

        eip712_domain_struct_hash = keccak(
            eip712_domain_struct_header
            + pad_20_bytes_to_32(to_bytes(hexstr=order.exchange_address))
        )

        eip712_order_struct_hash = keccak(
            eip712_order_schema_hash
            + pad_20_bytes_to_32(to_bytes(hexstr=order.maker_address))
            + pad_20_bytes_to_32(to_bytes(hexstr=order.taker_address))
            + pad_20_bytes_to_32(to_bytes(hexstr=order.fee_recipient_address))
            + pad_20_bytes_to_32(to_bytes(hexstr=order.sender_address))
            + int_to_32_big_endian_bytes(int(order.maker_asset_amount))
            + int_to_32_big_endian_bytes(int(order.taker_asset_amount))
            + int_to_32_big_endian_bytes(int(order.maker_fee))
            + int_to_32_big_endian_bytes(int(order.taker_fee))
            + int_to_32_big_endian_bytes(int(order.expiration_time_secs))
            + int_to_32_big_endian_bytes(int(order.salt))
            + keccak(to_bytes(hexstr=order.maker_asset_data))
            + keccak(to_bytes(hexstr=order.taker_asset_data))
        )

        return "0x" + keccak(
            eip191_header
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
