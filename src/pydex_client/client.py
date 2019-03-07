"""
PyDEX Client to interact with PyDEX app

author: officialcryptomaster@gmail.com
"""
import json
import requests
from zero_ex.json_schemas import assert_valid
from utils.zeroexutils import ZxWeb3Client

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20


class PyDexClient(ZxWeb3Client):
    """PyDEX Client to interact with PyDEX app"""

    __name__ = "PyDexClient"
    asset_pairs_url = "/v2/asset_pairs"
    fee_recipients_url = "/v2/fee_recipients"
    get_order_url = "/v2/order/"
    get_orders_url = "/v2/orders"
    orderbook_url = "/v2/orderbook"
    post_order_url = "/v2/order"

    def __init__(
        self,
        network_id,
        web3_rpc_url,
        private_key=None,
        pydex_api_url="http://localhost:3000",
    ):
        """Create a PyDexClient to interact with PyDEX exchange

        Keyword arguments:
        network_id -- numerable id of networkId convertible to `constants.NetworkId`
        web3_rpc_url -- string of the URL of the Web3 service
        private_key -- hex bytes or hex string of private key for signing transactions
            (must be convertible to `HexBytes`) (default: None)
        pydex_api_url -- string path to pyDEX app api server
            (default: "http://localhost:3000")
        """
        super(PyDexClient, self).__init__(
            network_id=network_id,
            web3_rpc_url=web3_rpc_url,
            private_key=private_key,
        )
        self._pydex_api_url = pydex_api_url
        if self._pydex_api_url.endswith("/"):
            self._pydex_api_url = self._pydex_api_url[:-1]

    def _str_arg_append(self):  # pylint: disable=no-self-use
        """String to append to list of params for `__str__`"""
        return f", pydex_api_url={self._pydex_api_url}"

    def make_asset_pairs_query(
        self,
        asset_data_a=None,
        asset_data_b=None,
        page=DEFAULT_PAGE,
        per_page=DEFAULT_PER_PAGE,
        include_maybe_fillables=False
    ):
        """Get a dict for querying the orderbook for relevant asset pairs

        Keyword arguments:
        asset_data_a -- hexstr value for the first asset in the pair (default: None)
        asset_data_b -- hexstr value for the second asset in the pair (default: None)
        page -- positive integer page number of paginated results (default: 1)
        per_page -- positive integer number of records per page (default: 20)
        include_maybe_fillables -- include signed_orders with order_status of 0 (default: False)
        """
        params = dict(
            assetDataA=asset_data_a,
            assetDataB=asset_data_b,
            networkId=self._network_id,
            page=page,
            per_page=per_page,
            include_maybe_fillables=include_maybe_fillables
        )
        return params

    def make_orders_query(  # pylint: disable=too-many-locals
        self,
        maker_asset_proxy_id=None,
        taker_asset_proxy_id=None,
        maker_asset_address=None,
        taker_asset_address=None,
        exchange_address=None,
        sender_address=None,
        maker_asset_data=None,
        taker_asset_data=None,
        trader_asset_data=None,
        maker_address=None,
        taker_address=None,
        trader_address=None,
        fee_recipient_address=None,
        page=DEFAULT_PAGE,
        per_page=DEFAULT_PER_PAGE,
        include_maybe_fillables=False
    ):
        """Get a dict for querying the orderbook for relevant asset pairs

        Keyword arguments:
        maker_asset_proxy_id -- hexstr proxy id for the maker asset (default: None)
        taker_asset_proxy_id -- hexstr proxy id for the taker asset (default: None)
        maker_asset_address -- hexstr address for maker asset (default: None)
        taker_asset_address -- hexstr address for taker asset (default: None)
        exchange_address -- hexstr address for the 0x exchange contract (default: None)
        sender_address -- hexstr address for the party reponsible to broadcast the order (default: None)
        maker_asset_data -- hexstr asset_data for maker side (default: None)
        taker_asset_data -- hexstr asset_data for taker side (default: None)
        trader_asset_data -- hexstr asset_data for either maker side or taker side (default: None)
        maker_address -- hexstr address for the maker (default: None)
        maker_address -- hexstr address for the taker (default: None)
        trader_address -- hexstr address for either maker or taker (default: None)
        fee_recipient_address -- hexstr address for the fee recipient (default: None)
        page -- positive integer page number of paginated results (default: 1)
        per_page -- positive integer number of records per page (default: 20)
        include_maybe_fillables -- include signed_orders with order_status of 0 (default: False)
        """
        params = dict(
            makerAssetProxyId=maker_asset_proxy_id,
            takerAssetProxyId=taker_asset_proxy_id,
            makerAssetAddress=maker_asset_address,
            takerAssetAddress=taker_asset_address,
            exchangeAddress=exchange_address,
            senderAddress=sender_address,
            makerAssetData=maker_asset_data,
            takerAssetData=taker_asset_data,
            traderAssetData=trader_asset_data,
            makerAddress=maker_address,
            takerAddress=taker_address,
            traderAddress=trader_address,
            feeRecipientAddress=fee_recipient_address,
            networkId=self._network_id,
            page=page,
            per_page=per_page,
            include_maybe_fillables=include_maybe_fillables
        )
        return params

    def make_orderbook_query(
        self,
        base_asset_data,
        quote_asset_data,
        full_set_asset_data=None,
        page=DEFAULT_PAGE,
        per_page=DEFAULT_PER_PAGE
    ):
        """Get a dict for querying the orderbook

        Keyword arguments:
        base_asset_data -- hexstr base asset data
        quote_asset_data -- hexstr quote asset data
        full_set_asset_data -- a dict with "LONG" and "SHORT" keys representing
            the full set of either the base or quote asset data (default: None)
        page -- positive integer page number of paginated results (default: 1)
        per_page -- positive integer number of records per page (default: 20)
        include_maybe_fillables -- include signed_orders with order_status of 0 (default: False)
        """
        params = dict(
            baseAssetData=base_asset_data,
            quoteAssetData=quote_asset_data,
            networkId=self._network_id,
            page=page,
            per_page=per_page
        )
        if full_set_asset_data:
            params["fullSetAssetData"] = json.dumps(full_set_asset_data)
        return params

    def get_orderbook(
        self,
        *args,
        **kwargs
    ):
        """Query the orderbook and return the result

        Keyword arguments:
        base_asset_data -- string base asset data
        quote_asset_data -- string quote asset data
        full_set_asset_data -- a dict with "LONG" and "SHORT" keys representing
            the full set of either the base or quote asset data (default: None)
        page -- positive integer page number of paginated results (default: 1)
        per_page -- positive integer number of records per page (default: 20)
        """
        params = self.make_orderbook_query(*args, **kwargs)
        response = requests.get(
            "{}{}".format(self._pydex_api_url, self.orderbook_url),
            params=params
        )
        return response.json()

    def post_signed_order(
        self,
        order
    ):
        """Validate and post a signed order to PyDEX app

        Keyword Arguments:
        order -- SignedOrder object to post
        """
        order_json = order.update().to_json()
        assert_valid(order_json, "/signedOrderSchema")
        res = requests.post(
            "{}{}".format(self._pydex_api_url, self.post_order_url),
            json=order_json
        )
        return res
