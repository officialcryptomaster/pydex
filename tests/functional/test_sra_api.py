"""
Tests for SRA interface

author: officialcryptomaster@gmail.com
"""
from zero_ex.json_schemas import assert_valid
from pydex_app.constants import DEFAULT_ERC20_DECIMALS, MAX_INT_STR, ZERO_STR
from pydex_app.db_models import SignedOrder


def test_post_order(
    test_client, pydex_client, make_veth_signed_order
):
    """Make sure posting order returns success and order exists
    in database."""
    order = make_veth_signed_order(
        asset_type="LONG",
        qty=0.0001,
        price=0.5,
        side="BUY",
    )
    res = test_client.post(
        pydex_client.post_order_url,
        json=order.to_json(),
    )
    assert res.status_code == 200
    # Retrieve order via get order endpoint
    res = test_client.get(
        "{}{}".format(pydex_client.get_order_url, order.hash)
    )
    assert res.status_code == 200
    assert res.get_json()["order"] == order.to_json()


def test_query_orderbook(
    test_client, pydex_client, asset_infos
):
    """Test whether the app can return a valid orderbook"""
    orderbook_params = pydex_client.make_orderbook_query(
        base_asset_data=asset_infos.VETH_ASSET_DATA,
        quote_asset_data=asset_infos.LONG_ASSET_DATA,
    )
    res = test_client.get(
        pydex_client.orderbook_url,
        query_string=orderbook_params
    )
    assert res.status_code == 200
    res = res.get_json()
    assert_valid(res, "/relayerApiOrderbookResponseSchema")
    # expected_res = {
    #     'asks': {'page': 1, 'perPage': 20, 'records': [], 'total': 0},
    #     'bids': {'page': 1, 'perPage': 20, 'records': [], 'total': 0}}
    # assert res == expected_res


def test_query_asset_pairs(
    test_client, pydex_client, asset_infos
):
    """Test whether the app can return valid asset pairs"""
    expected_res = {
        'total': 1,
        'page': 1,
        'perPage': 20,
        'records': [
            {
                'assetDataA': {
                    'minAmount': ZERO_STR,
                    'maxAmount': MAX_INT_STR,
                    'precision': DEFAULT_ERC20_DECIMALS,
                    'assetData': asset_infos.VETH_ASSET_DATA
                },
                'assetDataB': {
                    'minAmount': ZERO_STR,
                    'maxAmount': MAX_INT_STR,
                    'precision': DEFAULT_ERC20_DECIMALS,
                    'assetData': asset_infos.LONG_ASSET_DATA
                }
            }
        ]
    }
    asset_pairs_params = pydex_client.make_asset_pairs_query(
        asset_data_a=asset_infos.VETH_ASSET_DATA,
        asset_data_b=asset_infos.LONG_ASSET_DATA,
    )
    res = test_client.get(
        pydex_client.asset_pairs_url,
        query_string=asset_pairs_params
    )
    assert res.status_code == 200
    assert res.get_json() == expected_res
    asset_pairs_params = pydex_client.make_asset_pairs_query()
    res = test_client.get(
        pydex_client.asset_pairs_url,
        query_string=asset_pairs_params
    )
    assert res.status_code == 200
    assert res.get_json() == expected_res


def test_query_fee_recipients(
    test_client, pydex_client
):
    """Test if app can return valid fee recipient(s)"""
    res = test_client.get(
        pydex_client.fee_recipients_url
    )
    assert res.status_code == 200


def test_to_and_from_json_signed_order(
    pydex_client
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
