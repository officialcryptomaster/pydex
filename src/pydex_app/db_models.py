from pydex_app import db
from zero_ex.json_schemas import assert_valid
from zero_ex import order_utils as ou
from pydex_app.utils import ZERO_STR, MAX_INT_STR
from eth_utils import keccak, remove_0x_prefix, to_bytes
from decimal import Decimal


class SignedOrder(db.Model):
    # TODO(CM): consider using names which violate pep8 but make
    # it faster and easier to work with order_utils
    hash = db.Column(db.String(42), unique=True, primary_key=True)
    maker_address = db.Column(db.String(42), nullable=False)
    taker_address = db.Column(db.String(42), default=ou._Constants.null_address)
    # TODO(CM): Is 32 chars enough for fees?
    maker_fee = db.Column(db.String(32), default="0")
    taker_fee = db.Column(db.String(32), default="0")
    sender_address = db.Column(db.String(42), default=ou._Constants.null_address)
    maker_asset_amount = db.Column(db.String(128), nullable=False)
    taker_asset_amount = db.Column(db.String(128), nullable=False)
    # TODO(CM): Is 128 chars enough for asset data?
    maker_asset_data = db.Column(db.String(128), nullable=False)
    taker_asset_data = db.Column(db.String(128), nullable=False)
    # TODO(CM): Is 128 chars too much for the salt?
    salt = db.Column(db.String(128), nullable=False)
    exchange_address = db.Column(db.String(42), nullable=False)
    fee_recipient_address = db.Column(db.String(42), default=ou._Constants.null_address)
    expiration_time_secs = db.Column(db.Integer, nullable=False)
    # TODO(CM): Is 256 chars too much for the signature?
    signature = db.Column(db.String(256), nullable=False)
    bid_price = db.Column(db.String(128))
    ask_price = db.Column(db.String(128))
    _sort_price = None

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
        self.update_bid_price()
        self.update_ask_price()
        return self

    def update_hash(self):
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
        except:
            print()
            self.bid_price = default_price
        return self

    def update_ask_price(self, default_price=MAX_INT_STR):
        """Ask price is price of maker asset per unit of taker asset
        (i.e. price of maker asset the maker is asking to sell)
        """
        try:
            self.ask_price = "{:.18f}".format(
                Decimal(self.maker_asset_amount) / Decimal(self.taker_asset_amount))
        except:
            self.ask_price = default_price
        return self

    def set_bid_as_sort_price(self):
        self._sort_price = self.bid_price
        return self

    def set_ask_as_sort_price(self):
        self._sort_price = self.ask_price
        return self

    @classmethod
    def get_order_hash_hex(cls, order):
        def pad_20_bytes_to_32(twenty_bytes: bytes):
            return bytes(12) + twenty_bytes

        def int_to_32_big_endian_bytes(i: int):
            return i.to_bytes(32, byteorder="big")

        eip712_domain_struct_hash = keccak(
            ou._Constants.eip712_domain_struct_header
            + pad_20_bytes_to_32(to_bytes(hexstr=order.exchange_address))
        )

        eip712_order_struct_hash = keccak(
            ou._Constants.eip712_order_schema_hash
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
            ou._Constants.eip191_header
            + eip712_domain_struct_hash
            + eip712_order_struct_hash
        ).hex()

    @classmethod
    def from_json(cls, order_json, check_validity=False):
        order = cls()
        if check_validity:
            assert_valid(order_json, "/signedOrderSchema")
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
        order.signature = order_json["signature"]
        order.update()
        return order
