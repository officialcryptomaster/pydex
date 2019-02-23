"""
Database models of common objects

author: officialcryptomaster@gmail.com
"""
from decimal import Decimal
from enum import Enum
from zero_ex.json_schemas import assert_valid
from pydex_app.database import PYDEX_DB as db
from pydex_app.constants import NULL_ADDRESS
from pydex_app.constants import ZERO_STR, MAX_INT_STR
from utils.zeroexutils import ZeroExWeb3Client
from utils.miscutils import try_, now_epoch_msecs, epoch_secs_to_local_time_str, epoch_msecs_to_local_time_str


class OrderStatus(Enum):
    """Enumeration of order statuses.
    Guarantees that:
    - 0 means there is no obvious problems but it may be unfundable
    - positive status means order is confirmed to be fillable
    - negative status means order is confirmed to not be fillable
    """
    INVALID = -10  # We will probably never insert these into the database
    UNFILLABLE_UNFUNDED = -7
    UNFILLABLE_CANCELLED_PARTIALLY_FILLED = -6
    UNFILLABLE_CANCELLED = -5
    UNFILLABLE_EXPIRED_PARTIALLY_FILLED = -4
    UNFILLABLE_EXPIRED = -3
    UNFILLABLE_FILLED = -2
    UNFILLABLE = -1
    MAYBE_FILLABLE = 0
    FILLABLE = 1
    FILLABLE_FULLY = 2
    FILLABLE_PARTIALLY = 3


class SignedOrder(db.Model):
    """SignedOrder model which provides persistence and convenience
    methods around dealing with 0x SignedOrder type
    """
    hash = db.Column(db.String(42), unique=True, primary_key=True)  # pylint: disable=no-member
    # ETH addresses are 40 bytes (add 2 more bytes for leading '0x')
    maker_address = db.Column(db.String(42), nullable=False)  # pylint: disable=no-member
    taker_address = db.Column(db.String(42), default=NULL_ADDRESS)  # pylint: disable=no-member
    exchange_address = db.Column(db.String(42), nullable=False)  # pylint: disable=no-member
    fee_recipient_address = db.Column(db.String(42), default=NULL_ADDRESS)  # pylint: disable=no-member
    sender_address = db.Column(db.String(42), default=NULL_ADDRESS)  # pylint: disable=no-member
    # in theory, amounts can be 32 bytes, in practive, we will only allow 16 bytes
    maker_asset_amount = db.Column(db.String(32), nullable=False)  # pylint: disable=no-member
    taker_asset_amount = db.Column(db.String(32), nullable=False)  # pylint: disable=no-member
    # while in theory fees can be 32 bytes, in practice, we will allow 16 bytes
    maker_fee = db.Column(db.String(32), default="0")  # pylint: disable=no-member
    taker_fee = db.Column(db.String(32), default="0")  # pylint: disable=no-member
    # salt is 32 bytes or 256 bits which is at most 78 chars in decimal
    salt = db.Column(db.String(78), nullable=False)  # pylint: disable=no-member
    # integer seconds since unix epoch (interpret as UTC timestamp)
    expiration_time_secs = db.Column(db.Integer, nullable=False)  # pylint: disable=no-member
    # asset data for ERC20 is 36 bytes, and 68 bytes for ERC721, so that is a
    # maximum of 132 hex chars plus 2 chars for the leading '0x'
    maker_asset_data = db.Column(db.String(134), nullable=False)  # pylint: disable=no-member
    taker_asset_data = db.Column(db.String(134), nullable=False)  # pylint: disable=no-member
    signature = db.Column(db.String(256), nullable=False)  # pylint: disable=no-member
    bid_price = db.Column(db.String(32))  # pylint: disable=no-member
    ask_price = db.Column(db.String(32))  # pylint: disable=no-member
    # integer milliseconds since unix epoch when record was created (interpret as UTC timestamp)
    created_at = db.Column(db.Integer,  # pylint: disable=no-member
                           nullable=False,
                           default=now_epoch_msecs)
    # integer milliseconds since unix epoch since last update to record (interpret as UTC timestamp)
    last_updated_at = db.Column(db.Integer,  # pylint: disable=no-member
                                nullable=False,
                                default=now_epoch_msecs,
                                onupdate=now_epoch_msecs)
    # integer status from `OrderStatus` enum.
    order_status = db.Column(db.Integer,  # pylint: disable=no-member
                             index=True,
                             nullable=False,
                             default=OrderStatus.MAYBE_FILLABLE.value)
    # cumulative taker fill amount from order that has actually been filled
    fill_amount = db.Column(db.String(32))  # pylint: disable=no-member
    _sort_price = None  # not a DB column

    def __str__(self):
        return (
            f"[SignedOrder](hash={self.hash}"
            f" | order_status={try_(OrderStatus, self.order_status)}"
            f" | bid_price={self.bid_price}"
            f" | ask_price={self.ask_price}"
            f" | maker_asset_amount={self.maker_asset_amount}"
            f" | taker_asset_amount={self.taker_asset_amount}"
            f" | maker_asset_data={self.maker_asset_data}"
            f" | taker_asset_data={self.taker_asset_data}"
            f" | maker_address={self.maker_address}"
            f" | taker_address={self.taker_address}"
            f" | expires={try_(epoch_secs_to_local_time_str, self.expiration_time_secs)}"
            f" | create_at={try_(epoch_msecs_to_local_time_str, self.created_at)}"
            f" | last_updated_at={try_(epoch_msecs_to_local_time_str, self.last_updated_at)}"
        )

    __repr__ = __str__

    def to_json(
        self,
        include_hash=False,
        include_signature=True,
        # FOR TESTING ONLY!
        test_order_status=None,
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
        if test_order_status:
            order["test_order_status"] = test_order_status
        return order

    def update_bid_ask_prices(self):
        """Update the bid and ask prices and return the order for chaining"""
        self.update_bid_price()
        self.update_ask_price()
        return self

    def update_hash(self):
        """Update the hash of the order and return the order for chaining"""
        self.hash = self.get_order_hash(self)
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

    @property
    def sort_price(self):
        """Get a price for sorting orders
        This is useful for full set order which result in a mix of bids and asks
        (hint: make use of `set_bid_price_as_sort_price` and its equivalent
        `set_bid_price_as_sort_price`)
        """
        return self._sort_price

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
    def get_order_hash(cls, signed_order):
        """Returns hex string hash of 0x SignedOrder object"""
        return ZeroExWeb3Client.get_order_hash(signed_order.to_json())

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
        if "test_order_status" in order_json:
            order.order_status = order_json["test_order_status"]
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
