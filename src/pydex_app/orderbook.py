"""
Orderbook is the abstraction of an orderbook of signed orders used in pyDEX

author: officialcryptomaster@gmail.com
"""
from zero_ex.dev_utils import abi_utils
from pydex_app.constants import DEFAULT_ERC20_DECIMALS, DEFAULT_PAGE, DEFAULT_PER_PAGE
from pydex_app.constants import MAX_INT_STR, SELECTOR_LENGTH, ZERO_STR
from pydex_app.database import PYDEX_DB as db
from pydex_app.db_models import SignedOrder
from pydex_app.order_watcher_client import OrderWatcherClient as owc
from utils.miscutils import paginate


class Orderbook:
    """Abstraction for orderbook of signed orders"""
    _owc = owc()

    def __init__(self):
        pass

    @classmethod
    def get_order_by_hash_if_exists(cls, order_hash):
        """Retrieves a specific order by orderHash."""
        signed_order_if_exists = SignedOrder.query.get_or_404(order_hash)
        return {"order": signed_order_if_exists.to_json(), "metaData": {}}

    @classmethod
    def get_asset_pairs(
        cls,
        asset_data_a=None,
        asset_data_b=None,
        page=DEFAULT_PAGE,
        per_page=DEFAULT_PER_PAGE
    ):
        """Retrieves a list of available asset pairs and the information
        required to trade them
        """
        asset_pairs = []
        if asset_data_a and asset_data_b:
            asset_pairs = SignedOrder.query.with_entities(
                SignedOrder.maker_asset_data, SignedOrder.taker_asset_data
            ).filter_by(maker_asset_data=asset_data_a, taker_asset_data=asset_data_b)
        elif asset_data_a:
            asset_pairs = SignedOrder.query.with_entities(
                SignedOrder.maker_asset_data, SignedOrder.taker_asset_data).filter_by(maker_asset_data=asset_data_a)
        elif asset_data_b:
            asset_pairs = SignedOrder.query.with_entities(
                SignedOrder.maker_asset_data, SignedOrder.taker_asset_data).filter_by(taker_asset_data=asset_data_b)

        unique_asset_pairs = set(asset_pairs)

        def erc721_asset_data_to_asset(asset_data):
            return {
                "minAmount": ZERO_STR,
                "maxAmount": "1",
                "precision": 0,
                "assetData": asset_data
            }

        def erc20_asset_data_to_asset(asset_data):
            return {
                "minAmount": ZERO_STR,
                "maxAmount": MAX_INT_STR,
                "precision": DEFAULT_ERC20_DECIMALS,
                "assetData": asset_data
            }

        def asset_data_to_asset(asset_data):
            asset_proxy_id: str = asset_data[0:SELECTOR_LENGTH]
            if asset_proxy_id == abi_utils.method_id("ERC20Token", ["address"]):
                return erc20_asset_data_to_asset(asset_data)
            if asset_proxy_id == abi_utils.method_id("ERC721Token", ["address"]):
                return erc721_asset_data_to_asset(asset_data)
            raise ValueError(f"Invalid asset data {str(asset_data)}")

        def get_asset_pair_data(asset_pair):
            return {
                "assetDataA": asset_data_to_asset(asset_pair[0]),
                "assetDataB": asset_data_to_asset(asset_pair[1])
            }

        asset_pairs_data = [get_asset_pair_data(asset_pair) for asset_pair in list(unique_asset_pairs)]
        return paginate(asset_pairs_data, page=page, per_page=per_page), len(asset_pairs_data)

    @classmethod
    def add_order(cls, json_order):
        """Add order to database and order watcher"""
        order = SignedOrder.from_json(json_order, check_validity=True)
        cls._owc.add_order(signed_order=order.to_json())
        db.session.add(order)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member

    @classmethod
    def get_bids(
        cls,
        base_asset,
        quote_asset,
        full_asset_set=None,
        page=DEFAULT_PAGE,
        per_page=DEFAULT_PER_PAGE
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
        bids = SignedOrder.query.filter_by(
            maker_asset_data=quote_asset,
            taker_asset_data=base_asset,
        )
        bids_count = bids.count()
        bids = bids.order_by(
            # bid_price is price of taker_asset in units of maker_asset,
            # so we want highest price first
            SignedOrder.bid_price.desc()
        )
        if full_asset_set:
            eq_maker_asset, eq_taker_asset = cls.get_full_set_equivalent(
                maker_asset=quote_asset, taker_asset=base_asset,
                full_asset_set=full_asset_set
            )
            eq_asks = SignedOrder.query.filter_by(
                maker_asset_data=eq_maker_asset,
                taker_asset_data=eq_taker_asset
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
        page=DEFAULT_PAGE,
        per_page=DEFAULT_PER_PAGE
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
        asks = SignedOrder.query.filter_by(
            maker_asset_data=base_asset,
            taker_asset_data=quote_asset,
        )
        asks_count = asks.count()
        asks = asks.order_by(
            # ask_price is price of maker_asset in units of taker_asset,
            # so we want the lowest price first
            SignedOrder.ask_price
        )
        if full_asset_set:
            eq_maker_asset, eq_taker_asset = cls.get_full_set_equivalent(
                maker_asset=base_asset, taker_asset=quote_asset,
                full_asset_set=full_asset_set
            )
            eq_bids = SignedOrder.query.filter_by(
                maker_asset_data=eq_maker_asset,
                taker_asset_data=eq_taker_asset
            )
            asks_count += eq_bids.count()
            asks = [ask.set_ask_as_sort_price() for ask in asks]
            asks.extend([eq_bid.set_bid_as_sort_price() for eq_bid in eq_bids])
            asks = sorted(asks, key=lambda o: o.sort_price, reverse=True)
        return paginate(asks, page=page, per_page=per_page), asks_count

    '''
    @classmethod
    def get_orders(
        cls,
        filter_params,
        page=DEFAULT_PAGE,
        per_page=DEFAULT_PER_PAGE
    ):
        """Retrieves a list of orders given query parameters."""

        def order_to_api_order(signed_order):
            return {"metaData": {}, "order": signed_order}
        filter_object = {k: v for k, v in filter_params.items() if v is not None}
        orders = SignedOrder.query.filter_by(**filter_object)
        api_orders = map(order_to_api_order, orders)
        return paginate(api_orders, page=page, per_page=per_page)
    '''

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
