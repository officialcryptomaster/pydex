"""
PyDEX Client to interact with PyDEX app

author: officialcryptomaster@gmail.com
"""
import json
import requests
from web3 import Web3, HTTPProvider
from zero_ex.json_schemas import assert_valid


class PyDexClient:
    """PyDEX Client to interact with PyDEX app"""

    orderbook_url = "/v2/orderbook"
    post_order_url = "/v2/order"

    def __init__(
        self,
        network_id,
        web3_rpc_url,
        private_key,
        pydex_api_url="https://localhost:3000",
    ):
        """
        Keyword arguments:
        network_id -- integer ID of network
        web3_rpc_url -- url of web3 provider for executing orders
        private_key -- string private key of wallet to sign orders
        pydex_api_url -- string path to pyDEX app api server
            (default: "https://localhost:3000")
        """
        self._network_id = network_id
        self._web3_rpc_url = web3_rpc_url
        self.__private_key = private_key
        self._pydex_api_url = pydex_api_url
        if self._pydex_api_url.endswith("/"):
            self._pydex_api_url = self._pydex_api_url[:-1]
        self._web3_provider = HTTPProvider(self._web3_rpc_url)
        self._web3 = Web3(self._web3_provider)
        self._web3_eth = self._web3.eth  # pylint: disable=no-member
        self._acct = self._web3_eth.account.privateKeyToAccount(self.__private_key)

    def make_orderbook_query(
        self,
        base_asset_data,
        quote_asset_data,
        full_set_asset_data=None,
        page=1,
        per_page=20
    ):
        """Get a dict for querying the orderbook

        Keyword arguments:
        base_asset_data -- string base asset data
        quote_asset_data -- string quote asset data
        full_set_asset_data -- a dict with "LONG" and "SHORT" keys representing
            the full set of either the base or quote asset data (default: None)
        page -- positive integer page number of paginated results (default: 1)
        per_page -- positive integer number of records per page (default: 20)
        """
        params = dict(
            baseAssetData=base_asset_data,
            quoteAssetData=quote_asset_data,
            networkId=self._network_id,
            page=page,
            per_page=per_page,
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
        order_json = order.to_json()
        assert_valid(order, "/signedOrderSchema")
        res = requests.post(
            "{}{}".format(self._pydex_api_url, self.post_order_url),
            json=order_json
        )
        return res
