"""
Orderbook is the abstraction of an orderbook of signed orders used in pyDEX

author: officialcryptomaster@gmail.com
"""
from pydex_app.database import PYDEX_DB as db
from pydex_app.db_models import SignedOrder
from utils.miscutils import paginate


class Orderbook:
    """Abstraction for orderbook of signed orders"""

    @classmethod
    def add_order(cls, order):
        """Add order to database without any validity checks.
        Note: OrderStatusHandler will check the status and activate orders
        by adding them to handler"""
        db.session.add(order)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member

    @classmethod
    def get_bids(
        cls,
        base_asset,
        quote_asset,
        full_asset_set=None,
        page=1,
        per_page=10
    ):
        """Get all bids to buy a `base_asset` by providing the `quote_asset`
        (i.e. bid is someone trying to buy the `base_asset` (`taker_asset`)
        by supplying the `quote_asset` (`maker_asset`).

        Keyword arguments:
        base_asset -- string asset_data to buy (i.e. `taker_asset_data`)
        quote_asset -- string asset_data to give in return (i.e. `maker_asset_data`)
        full_asset_set -- dict with 'LONG' and 'SHORT' keys pointing to
            the long and short asset_data that make up the full set. (one of
            these must match the maker to taker asset, or will cause an
            exception to be thrown)
        """
        bids = SignedOrder.query.filter(
            (SignedOrder.maker_asset_data == quote_asset)
            & (SignedOrder.taker_asset_data == base_asset)
            & (SignedOrder.order_status > 0)
        )
        bids_count = bids.count()
        bids = bids.order_by(
            # bid_price is price of taker_asset in units of maker_asset,
            # so we want highest price first
            SignedOrder.bid_price.desc()
        )
        if full_asset_set:
            eq_maker_asset, eq_taker_asset = cls.get_full_set_equivalent(
                maker_asset=quote_asset,
                taker_asset=base_asset,
                full_asset_set=full_asset_set
            )
            eq_asks = SignedOrder.query.filter(
                (SignedOrder.maker_asset_data == eq_maker_asset)
                & (SignedOrder.taker_asset_data == eq_taker_asset)
                & (SignedOrder.order_status > 0)
            )
            bids_count += eq_asks.count()
            bids = [bid.set_bid_as_sort_price() for bid in bids]
            bids.extend([eq_ask.set_ask_as_sort_price() for eq_ask in eq_asks])
            bids = sorted(bids, key=lambda o: o.sort_price, reverse=True)
        return paginate(bids, page=page, per_page=per_page), bids_count

    @classmethod
    def get_asks(
        cls,
        base_asset,
        quote_asset,
        full_asset_set=None,
        page=1,
        per_page=10
    ):
        """Get all asks to sell a `base_asset` against a `quote_asset`
        (i.e. ask is someone trying to sell the `base_asset` (`maker_asset`)
        by collecting the `quote_asset` (`taker_asset`))

        Keyword arguments:
        base_asset -- string asset_data to sell (i.e. `make_asset_data`)
        quote_asset -- string asset_data to get in return (i.e. `taker_asset_data`)
        full_asset_set -- dict with 'LONG' and 'SHORT' keys pointing to
            the long and short asset_data that make up the full set. (one of
            these must match the maker to taker asset, or will cause an
            exception to be thrown)
        """
        asks = SignedOrder.query.filter(
            (SignedOrder.maker_asset_data == base_asset)
            & (SignedOrder.taker_asset_data == quote_asset)
            & (SignedOrder.order_status > 0)
        )
        asks_count = asks.count()
        asks = asks.order_by(
            # ask_price is price of maker_asset in units of taker_asset,
            # so we want the lowest price first
            SignedOrder.ask_price
        )
        if full_asset_set:
            eq_maker_asset, eq_taker_asset = cls.get_full_set_equivalent(
                maker_asset=base_asset,
                taker_asset=quote_asset,
                full_asset_set=full_asset_set
            )
            eq_bids = SignedOrder.query.filter(
                (SignedOrder.maker_asset_data == eq_maker_asset)
                & (SignedOrder.taker_asset_data == eq_taker_asset)
                & (SignedOrder.order_status > 0)
            )
            asks_count += eq_bids.count()
            asks = [ask.set_ask_as_sort_price() for ask in asks]
            asks.extend([eq_bid.set_bid_as_sort_price() for eq_bid in eq_bids])
            asks = sorted(asks, key=lambda o: o.sort_price, reverse=True)
        return paginate(asks, page=page, per_page=per_page), asks_count

    @classmethod
    def get_full_set_equivalent(cls, maker_asset, taker_asset, full_asset_set):
        """Given a maker and taker assets and a full asset set, returns
        the maker and taker assets which is the equivalent but using the
        complimentary asset from the full set.

        Keyword Args:
        maker_asset -- string of maker asset id (a.k.a asset_data in 0x)
        taker_asset -- string of taker asset id (a.k.a asset_data in 0x)
        full_asset_set -- dict with 'LONG' and 'SHORT' keys pointing to
            the long and short asset_data that make up the full set. (one of
            these must match the maker to taker asset, or will cause an
            exception to be thrown)
        """
        long_asset = full_asset_set["LONG"]
        short_asset = full_asset_set["SHORT"]
        if maker_asset == long_asset:
            maker_asset = taker_asset
            taker_asset = short_asset
        elif maker_asset == short_asset:
            maker_asset = taker_asset
            taker_asset = long_asset
        else:
            if taker_asset == long_asset:
                taker_asset = maker_asset
                maker_asset = short_asset
            elif taker_asset == short_asset:
                taker_asset = maker_asset
                maker_asset = long_asset
            else:
                raise ValueError(
                    "Neither make or taker assets matched the assets provided"
                    "in the full set")
        return (maker_asset, taker_asset)
