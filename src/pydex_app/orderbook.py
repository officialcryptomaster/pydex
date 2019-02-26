"""
Orderbook is the abstraction of an orderbook of signed orders used in pyDEX

author: officialcryptomaster@gmail.com
"""
from zero_ex.dev_utils import abi_utils
from zero_ex.order_utils import asset_data_utils as adu
from pydex_app.constants import DEFAULT_ERC20_DECIMALS, DEFAULT_PAGE, DEFAULT_PER_PAGE
from pydex_app.constants import MAX_INT_STR, SELECTOR_LENGTH, ZERO_STR
from pydex_app.database import PYDEX_DB as db
from pydex_app.db_models import SignedOrder
from utils.miscutils import normalize_query_param, paginate, to_api_order


class Orderbook:
    """Abstraction for orderbook of signed orders"""

    @classmethod
    def get_order_by_hash(cls, order_hash):
        """Retrieves a specific order by orderHash. Return 404 error if no matching
        signed order is found.

        Keyword arguments:
        order_hash -- string hash of the signed order to be queried
        """
        signed_order = SignedOrder.query.get_or_404(normalize_query_param(order_hash))
        return to_api_order(signed_order.to_json())

    @classmethod
    def get_asset_pairs(  # pylint: disable=too-many-locals
        cls,
        asset_data_a=None,
        asset_data_b=None,
        page=DEFAULT_PAGE,
        per_page=DEFAULT_PER_PAGE
    ):
        """Retrieves a list of available asset pairs and the information
        required to trade them.

        Keyword arguments:
        asset_data_a -- string asset_data for maker side (i.e. `maker_asset_data`) (default: None)
        asset_data_b -- string asset_data for taker side (i.e. `taker_asset_data`) (default: None)
        page -- positive integer page number of paginated results (default: 1)
        per_page -- positive integer number of records per page (default: 20)
        """
        asset_pairs = []
        normalized_asset_a = normalize_query_param(asset_data_a)
        normalized_asset_b = normalize_query_param(asset_data_b)

        query_filter = SignedOrder.order_status > 0
        if asset_data_a:
            query_filter &= SignedOrder.maker_asset_data == normalized_asset_a
        if asset_data_b:
            query_filter &= SignedOrder.taker_asset_data == normalized_asset_b
        asset_pairs = SignedOrder.query.with_entities(
            SignedOrder.maker_asset_data,
            SignedOrder.taker_asset_data
        ).filter(query_filter)
        unique_asset_pairs = set(sorted(asset_pairs))

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
            asset_proxy_id: str = asset_data[:SELECTOR_LENGTH]
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
    def add_order(cls, order_json):
        """Add order to database without any validity checks.
        Note: OrderStatusHandler will check the status and activate orders
        by adding them to handler

        Keyword arguments:
        order_json -- json representation of the SignedOrder
        """
        order = SignedOrder.from_json(order_json, check_validity=True)
        db.session.add(order)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member

    @classmethod
    def get_bids(  # pylint: disable=too-many-locals
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
        page -- positive integer page number of paginated results (default: 1)
        per_page -- positive integer number of records per page (default: 20)
        """
        normalized_quote_asset = normalize_query_param(quote_asset)
        normalized_base_asset = normalize_query_param(base_asset)
        bids = SignedOrder.query.filter(
            (SignedOrder.maker_asset_data == normalized_quote_asset)
            & (SignedOrder.taker_asset_data == normalized_base_asset)
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
                maker_asset=normalized_quote_asset,
                taker_asset=normalized_base_asset,
                full_asset_set=full_asset_set
            )
            normalized_eq_maker_asset = normalize_query_param(eq_maker_asset)
            normalized_eq_taker_asset = normalize_query_param(eq_taker_asset)
            eq_asks = SignedOrder.query.filter(
                (SignedOrder.maker_asset_data == normalized_eq_maker_asset)
                & (SignedOrder.taker_asset_data == normalized_eq_taker_asset)
                & (SignedOrder.order_status > 0)
            )
            bids_count += eq_asks.count()
            bids = [bid.set_bid_as_sort_price() for bid in bids]
            bids.extend([eq_ask.set_ask_as_sort_price() for eq_ask in eq_asks])
            bids = sorted(bids, key=lambda o: o.sort_price, reverse=True)
        return paginate(bids, page=page, per_page=per_page), bids_count

    @classmethod
    def get_asks(  # pylint: disable=too-many-locals
        cls,
        base_asset,
        quote_asset,
        full_asset_set=None,
        page=DEFAULT_PAGE,
        per_page=DEFAULT_PER_PAGE
    ):
        """Get all asks to sell a `base_asset` against a `quote_asset`
        (i.e. ask is someone trying to sell the `base_asset` (`maker_asset`)
        by collecting the `quote_asset` (`taker_asset`)).

        Keyword arguments:
        base_asset -- string asset_data to sell (i.e. `make_asset_data`)
        quote_asset -- string asset_data to get in return (i.e. `taker_asset_data`)
        full_asset_set -- dict with 'LONG' and 'SHORT' keys pointing to
            the long and short asset_data that make up the full set. (one of
            these must match the maker to taker asset, or will cause an
            exception to be thrown)
        page -- positive integer page number of paginated results (default: 1)
        per_page -- positive integer number of records per page (default: 20)
        """
        normalized_quote_asset = normalize_query_param(quote_asset)
        normalized_base_asset = normalize_query_param(base_asset)
        asks = SignedOrder.query.filter(
            (SignedOrder.maker_asset_data == normalized_base_asset)
            & (SignedOrder.taker_asset_data == normalized_quote_asset)
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
                maker_asset=normalized_base_asset,
                taker_asset=normalized_quote_asset,
                full_asset_set=full_asset_set
            )
            normalized_eq_maker_asset = normalize_query_param(eq_maker_asset)
            normalized_eq_taker_asset = normalize_query_param(eq_taker_asset)
            eq_bids = SignedOrder.query.filter(
                (SignedOrder.maker_asset_data == normalized_eq_maker_asset)
                & (SignedOrder.taker_asset_data == normalized_eq_taker_asset)
                & (SignedOrder.order_status > 0)
            )
            asks_count += eq_bids.count()
            asks = [ask.set_ask_as_sort_price() for ask in asks]
            asks.extend([eq_bid.set_bid_as_sort_price() for eq_bid in eq_bids])
            asks = sorted(asks, key=lambda o: o.sort_price, reverse=True)
        return paginate(asks, page=page, per_page=per_page), asks_count

    @classmethod
    def get_orders(  # pylint: disable=too-many-locals
        cls,
        maker_asset_proxy_id=None,
        taker_asset_proxy_id=None,
        maker_asset_address=None,
        taker_asset_address=None,
        exchange_address=None,
        sender_address=None,
        maker_asset_data=None,
        taker_asset_data=None,
        maker_address=None,
        taker_address=None,
        fee_recipient_address=None,
        page=DEFAULT_PAGE,
        per_page=DEFAULT_PER_PAGE
    ):
        """Retrieves a list of orders given query parameters.

        Keyword arguments:
        maker_asset_proxy_id -- string proxy id for the maker asset (default: None)
        taker_asset_proxy_id -- string proxy id for the taker asset (default: None)
        maker_asset_address -- string address for maker asset (default: None)
        taker_asset_address -- string address for taker asset (default: None)
        exchange_address -- string address for the 0x exchange contract (default: None)
        sender_address -- string address for the party reponsible to broadcast the order (default: None)
        maker_asset_data -- string asset_data for maker side (default: None)
        taker_asset_data -- string asset_data for taker side (default: None)
        maker_address -- string address for the maker (default: None)
        maker_address -- string address for the taker (default: None)
        fee_recipient_address -- string address for the fee recipient (default: None)
        page -- positive integer page number of paginated results (default: 1)
        per_page -- positive integer number of records per page (default: 20)
        """
        pre_filter = dict(
            exchange_address=normalize_query_param(exchange_address),
            sender_address=normalize_query_param(sender_address),
            maker_asset_data=normalize_query_param(maker_asset_data)
            or (adu.encode_erc20_asset_data(maker_asset_address) if maker_asset_address else None),
            taker_asset_data=normalize_query_param(taker_asset_data)
            or (adu.encode_erc20_asset_data(taker_asset_address) if taker_asset_address else None),
            maker_address=normalize_query_param(maker_address),
            taker_address=normalize_query_param(taker_address),
            fee_recipient_address=normalize_query_param(fee_recipient_address)
        )
        filter_object = {k: v for k, v in pre_filter.items() if v is not None}
        normalized_maker_asset_proxy_id = normalize_query_param(maker_asset_proxy_id)
        normalized_taker_asset_proxy_id = normalize_query_param(taker_asset_proxy_id)
        query_filter = SignedOrder.order_status > 0
        if maker_asset_proxy_id:
            query_filter &= SignedOrder.maker_asset_data.startswith(normalized_maker_asset_proxy_id)
        if taker_asset_proxy_id:
            query_filter &= SignedOrder.taker_asset_data.startswith(normalized_taker_asset_proxy_id)
        orders = SignedOrder.query.filter(query_filter).filter_by(**filter_object)
        api_orders = [to_api_order(order.to_json()) for order in orders]
        return paginate(api_orders, page=page, per_page=per_page), len(api_orders)

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
