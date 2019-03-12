"""
Database models of common objects

author: officialcryptomaster@gmail.com
"""
from enum import Enum
from pydex_app.database import PYDEX_DB as db
from utils.miscutils import try_, now_epoch_msecs, epoch_msecs_to_local_time_str
from utils.web3utils import NULL_ADDRESS
from utils.zeroexutils import ZxSignedOrder


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


DB_COL = db.Column  # pylint: disable=no-member
DB_STR = db.String  # pylint: disable=no-member
DB_INT = db.Integer  # pylint: disable=no-member


class SignedOrder(ZxSignedOrder, db.Model):
    """SignedOrder model which provides persistence and convenience
    methods around dealing with 0x SignedOrder type
    """
    hash_ = DB_COL("hash", DB_STR(64), unique=True, primary_key=True)
    # ETH addresses are 42 bytes (includes leading '0x')
    maker_address_ = DB_COL("maker_address", DB_STR(42), nullable=False)
    taker_address_ = DB_COL("taker_address", DB_STR(42), default=NULL_ADDRESS)
    fee_recipient_address_ = DB_COL("fee_recipient_address", DB_STR(42), default=NULL_ADDRESS)
    sender_address_ = DB_COL("sender_address", DB_STR(42), default=NULL_ADDRESS)
    exchange_address_ = DB_COL("exchange_address", DB_STR(42), nullable=False)
    # in theory, amounts can be 32 bytes, in practice, we will only allow 32 decimal chars
    maker_asset_amount_ = DB_COL("maker_asset_amount", DB_STR(32), nullable=False, default="0")
    taker_asset_amount_ = DB_COL("taker_asset_amount", DB_STR(32), nullable=False, default="0")
    # while in theory fees can be 32 bytes, in practice, we will allow 32 decimal chars
    maker_fee_ = DB_COL("maker_fee", DB_STR(32), default="0")
    taker_fee_ = DB_COL("taker_fee", DB_STR(32), default="0")
    # salt is 32 bytes or 256 bits which is at most 78 decimal chars
    salt_ = DB_COL("salt", DB_STR(78), nullable=False)
    # integer seconds since unix epoch (interpret as UTC timestamp)
    expiration_time_secs_ = DB_COL("expiration_time_secs", DB_INT, nullable=False)
    # asset data for ERC20 is 36 bytes, and 68 bytes for ERC721, so that is a
    # maximum of 138 hex chars  (includes leading '0x')
    maker_asset_data_ = DB_COL("maker_asset_data", DB_STR(138), nullable=False)
    taker_asset_data_ = DB_COL("taker_asset_data", DB_STR(138), nullable=False)
    signature_ = DB_COL("signature", DB_STR(256), nullable=False)
    bid_price_ = DB_COL("bid_price", DB_STR(32))
    ask_price_ = DB_COL("ask_price", DB_STR(32))
    # integer milliseconds since unix epoch when record was created (interpret as UTC timestamp)
    created_at_msecs_ = DB_COL("created_at_msecs", DB_INT, nullable=False, default=now_epoch_msecs)
    # integer milliseconds since unix epoch since last update to record (interpret as UTC timestamp)
    last_updated_at_msecs_ = DB_COL("last_updated_at_msecs",
                                    DB_INT,
                                    nullable=False,
                                    default=now_epoch_msecs,
                                    onupdate=now_epoch_msecs)
    # integer status from `OrderStatus` enum.
    order_status_ = DB_COL("order_status",
                           DB_INT,
                           index=True,
                           nullable=False,
                           default=OrderStatus.MAYBE_FILLABLE.value)
    # cumulative taker fill amount from order that has actually been filled
    _fill_amount = DB_COL(DB_STR(32))  # pylint: disable=no-member

    def __str__(self):
        return (
            f"[SignedOrder]"
            f"(hash={self.hash}"
            f" | order_status={try_(OrderStatus, self.order_status)}"
            f" | bid_price={self.bid_price}"
            f" | ask_price={self.ask_price}"
            f" | maker_asset_amount={self.maker_asset_amount}"
            f" | taker_asset_amount={self.taker_asset_amount}"
            f" | maker_asset_data={self.maker_asset_data}"
            f" | taker_asset_data={self.taker_asset_data}"
            f" | maker_address={self.maker_address}"
            f" | taker_address={self.taker_address}"
            f" | signature={self.signature}"
            f" | expires={self.expiration_time}"
            f" | create_at={self.created_at}"
            f" | last_updated_at={self.last_updated_at}"
            ")"
        )

    __repr__ = __str__

    @property
    def last_updated_at_msecs(self):
        """Get last update time as milliseconds from epoch"""
        return self.last_updated_at_msecs_

    @property
    def last_updated_at(self):
        """Get last update time timestamp as naive DateTime"""
        return try_(epoch_msecs_to_local_time_str, self.last_updated_at_msecs_)

    @property
    def order_status(self):
        """Get order status as OrderStatusEnum"""
        return self.order_status_

    @order_status.setter
    def order_status(self, value):
        """Set the order status"""
        if not isinstance(value, OrderStatus):
            value = OrderStatus(value)
        self.order_status_ = value.value

    @property
    def fill_amount(self):
        """Get taker fill amount as Decimal in base units"""
        return try_(int, self.fill_amount_, _default=0)
