# src needs to be in path

from pydex_app.db_models import SignedOrder
from zero_ex.order_utils import generate_order_hash_hex, order_to_jsdict, make_empty_order, _Constants

from pydex_app import db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from web3 import Web3

def test_order():
    #make sure we can use utils correctly
    empty_order = make_empty_order()
    order_json = order_to_jsdict(empty_order)
    assert order_json == {
        "makerAddress": _Constants.null_address,
        "takerAddress": _Constants.null_address,
        "senderAddress": _Constants.null_address,
        "feeRecipientAddress": _Constants.null_address,
        "makerAssetData": "0x0000000000000000000000000000000000000000",
        "takerAssetData": "0x0000000000000000000000000000000000000000",
        "salt": 0,
        "makerFee": 0,
        "takerFee": 0,
        "makerAssetAmount": 0,
        "takerAssetAmount": 0,
        "expirationTimeSeconds": 0,
        'exchangeAddress': '0x0000000000000000000000000000000000000000',
    }

    actual_hash_hex = generate_order_hash_hex(empty_order, "0x0000000000000000000000000000000000000000")
    expected_hash_hex = "faa49b35faeb9197e9c3ba7a52075e6dad19739549f153b77dfcf59408a4b422"
    assert actual_hash_hex == expected_hash_hex

    o = SignedOrder.from_json(order_json,include_signature=False)    
    assert o.to_json(include_signature=False) == order_json
    o.update_hash()
    #why needs prefix "0x"?
    assert o.hash == "0x" + expected_hash_hex
    

def test_sql():
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()
    #ERROR 'Engine' object is not iterable
    #db.create_all(engine)
    
    