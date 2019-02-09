# src needs to be in path

from pydex_app.db_models import SignedOrder
from zero_ex.order_utils import generate_order_hash_hex, make_empty_order

#from sqlalchemy import create_engine

def test_order():
    #make sure we can use utils correctly
    actual_hash_hex = generate_order_hash_hex(make_empty_order(), "0x0000000000000000000000000000000000000000")
    expected_hash_hex = "faa49b35faeb9197e9c3ba7a52075e6dad19739549f153b77dfcf59408a4b422"
    assert actual_hash_hex == expected_hash_hex

    o = SignedOrder()
    assert o.maker_address == None        
    

def test_sql():
    pass

    """
    engine = create_engine('sqlite:///:memory:')
    session.configure(bind=engine)
    model.metadata.create_all(engine)
    """
