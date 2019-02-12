"""
Tests for SRA interface

author: officialcryptomaster@gmail.com
"""
from zero_ex.json_schemas import assert_valid
from pydex_client.client import PyDexClient
from pydex_app.db_models import SignedOrder


def test_query_orderbook(
    test_client, pydex_client, asset_infos
):
    """Test whether the app can return a valid orderbook"""
    orderbook_params = pydex_client.make_orderbook_query(
        base_asset_data=asset_infos.VETH_ASSET_DATA,
        quote_asset_data=asset_infos.LONG_ASSET_DATA,
    )
    res = test_client.get(
        PyDexClient.orderbook_url,
        query_string=orderbook_params)
    assert res.status_code == 200
    res = res.get_json()
    assert_valid(res, "/relayerApiOrderbookResponseSchema")
    # expected_res = {
    #     'asks': {'page': 1, 'perPage': 20, 'records': [], 'total': 0},
    #     'bids': {'page': 1, 'perPage': 20, 'records': [], 'total': 0}}
    # assert res == expected_res


def test_post_order(
    test_client, pydex_client, make_veth_signed_order
):
    """Make sure posting order returns success and order exists
    in database.
    """
    order = make_veth_signed_order(
        asset_type="LONG",
        qty=0.0001,
        price=0.45,
        side="BUY",
    )
    res = test_client.post(
        pydex_client.post_order_url,
        json=order.to_json(),
    )
    assert res.status_code == 200
    assert SignedOrder.query.filter_by(
        hash=order.hash
    ).count() == 1
