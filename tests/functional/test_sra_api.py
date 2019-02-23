"""
Tests for SRA interface
author: officialcryptomaster@gmail.com
"""
from zero_ex.json_schemas import assert_valid
from pydex_client.client import PyDexClient
from pydex_app.db_models import SignedOrder

SIDE_BUY = "BUY"
SIDE_SELL = "SELL"
ASSET_LONG = "LONG"
ASSET_SHORT = "SHORT"

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


def test_to_and_from_json_signed_order(
    pydex_client,
):
    """Make sure creating a signed order from json does not change when it is turned back to json"""
    expected_order_json = {
        'makerAddress': '0x5409ed021d9299bf6814279a6a1411a7e866a631',
        'takerAddress': '0x0000000000000000000000000000000000000000',
        'makerFee': '0',
        'takerFee': '0',
        'senderAddress': '0x0000000000000000000000000000000000000000',
        'makerAssetAmount': '50000000000000',
        'takerAssetAmount': '100000000000000',
        'makerAssetData': '0xf47261b0000000000000000000000000c4abc01578139e2105d9c9eba0b0aa6f6a60d082',
        'takerAssetData': '0xf47261b0000000000000000000000000358b48569a4a4ef6310c1f1d8e50be9d068a50c6',
        'exchangeAddress': '0xbce0b5f6eb618c565c3e5f5cd69652bbc279f44e',
        'salt': '314725192512133120',
        'feeRecipientAddress': '0x0000000000000000000000000000000000000000',
        'expirationTimeSeconds': 1550439701,
        'hash': '0x3fbc553ade14a36ba6e5055817d44170797c560e62d0db5c79aa0739732c8199',
        'signature': (
            '0x1c4f65f2bfbf384e783cbb62ef27e7091fa02d9fa9ad1299670f05582325e027b'
            '9261afef5bceed9e0c84a92aeeead35df85b1cf174a02f0f3d2935c73552ac28803'),
    }
    # make a new SignedOrder object without the signature of hash
    order = SignedOrder.from_json(
        {k: v for k, v in expected_order_json.items()
         if k not in ["signature", "hash"]},
        include_signature=False,
    )
    print(pydex_client.private_key)
    print(order.update().hash)
    # sign the order
    order.signature = pydex_client.sign_hash_0x_compat(order.update().hash)
    assert order.to_json(include_hash=True) == expected_order_json


def test_post_order(
    test_client, pydex_client, make_veth_signed_order
):
    """Make sure posting order returns success and order exists
    in database."""
    order = make_veth_signed_order(
        asset_type=ASSET_LONG,
        qty=0.0001,
        price=0.5,
        side=SIDE_BUY,
    )
    res = test_client.post(
        pydex_client.post_order_url,
        json=order.to_json(),
    )
    assert res.status_code == 200
    assert SignedOrder.query.filter_by(
        hash=order.hash
    ).count() == 1

    order_short = make_veth_signed_order(
        asset_type=ASSET_SHORT,
        qty=0.0002,
        price=0.9,
        side=SIDE_BUY,
    )
    res = test_client.post(
        pydex_client.post_order_url,
        json=order_short.to_json(),
    )
    assert res.status_code == 200
    assert SignedOrder.query.filter_by(
        hash=order_short.hash
    ).count() == 1

    assert SignedOrder.query.count() == 2

    order_sell = make_veth_signed_order(
        asset_type=ASSET_LONG,
        qty=0.0001,
        price=0.5,
        side=SIDE_SELL,
    )
    res = test_client.post(
        pydex_client.post_order_url,
        json=order_sell.to_json(),
    )
    assert res.status_code == 200
    assert SignedOrder.query.filter_by(
        hash=order_sell.hash
    ).count() == 1

    assert SignedOrder.query.count() == 3
    
    order_short_sell = make_veth_signed_order(
        asset_type=ASSET_SHORT,
        qty=0.0001,
        price=0.5,
        side=SIDE_SELL,
    )
    res = test_client.post(
        pydex_client.post_order_url,
        json=order_short_sell.to_json(),
    )
    assert res.status_code == 200
    assert SignedOrder.query.filter_by(
        hash=order_short_sell.hash
    ).count() == 1

    assert SignedOrder.query.count() == 4