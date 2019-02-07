from pydex_app import app, db
from flask import request
from flask_cors import cross_origin
from pydex_app.db_models import SignedOrder
from pydex_app.orderbook import OrderBook
from zero_ex import order_utils as ou
from zero_ex.json_schemas import assert_valid
import pydex_app.utils as pdu
import json


@app.route("/")
def hello():
    return """
    <div>
        <h1>PyDEX Relayer</h1>
        <a href="http://sra-spec.s3-website-us-east-1.amazonaws.com">
            Check API reference...
        </a>
    </div>
    """

# GET AssetPairs endpoint retrieves a list of available asset pairs and the information required to trade them.
# http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getAssetPairs
@app.route("/v2/asset_pairs", methods=["GET"])
@cross_origin()
def get_asset_pairs():
    raise NotImplementedError()

# GET Orders endpoint retrieves a list of orders given query parameters.
# http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrders
@app.route("/v2/orders", methods=["GET"])
def get_orders():
    raise NotImplementedError()

# GET Orderbook endpoint retrieves the orderbook for a given asset pair.
# http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrderbook
@app.route('/v2/orderbook', methods=["GET"])
@cross_origin()
def get_order_book():
    print("############ GETTING ORDER BOOK")
    network_id = request.args.get("networkId", app.config["PYDEX_NETWORK_ID"])
    assert network_id == app.config["PYDEX_NETWORK_ID"], f"networkId={network_id} not supported"
    page = int(request.args.get("page", app.config["OB_DEFAULT_PAGE"]))
    per_page = int(request.args.get("per_page", app.config["OB_DEFAULT_PER_PAGE"]))
    base_asset = request.args["baseAssetData"]
    quote_asset = request.args["quoteAssetData"]
    full_asset_set = request.args.get("fullSetAssetData")
    if full_asset_set:
        full_asset_set = json.loads(full_asset_set)
    bids, tot_bid_count = OrderBook.get_bids(
        base_asset=base_asset,
        quote_asset=quote_asset,
        full_asset_set=full_asset_set,
        page=page,
        per_page=per_page)
    asks, tot_ask_count = OrderBook.get_asks(
        base_asset=base_asset,
        quote_asset=quote_asset,
        full_asset_set=full_asset_set,
        page=page,
        per_page=per_page)
    res = {
        "bids": {
            "total": tot_bid_count,
            "perPage": per_page,
            "page": page,
            "records": [
                {"order": bid.to_json(), "metaData": {}}
                for bid in bids
            ],
        },
        "asks": {
            "total": tot_ask_count,
            "perPage": per_page,
            "page": page,
            "records": [
                {"order": ask.to_json(), "metaData": {}}
                for ask in asks
            ],
        }
    }
    return json.dumps(res)

# POST Order config endpoint retrives the values for order fields that the relayer requires.
# http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrderConfig
@app.route('/v2/order_config', methods=["POST"])
@cross_origin()
def post_order_config():
    print("############ GETTING ORDER CONFIG")
    network_id = request.args.get("networkId", app.config["PYDEX_NETWORK_ID"])
    assert network_id == app.config["PYDEX_NETWORK_ID"], f"networkId={network_id} not supported"
    order = request.json
    assert_valid(order, "/orderConfigRequestSchema")
    res = {
        "senderAddress": ou._Constants.null_address,
        "feeRecipientAddress": app.config["PYDEX_ZRX_FEE_RECIPIENT"],
        "makerFee": app.config["PYDEX_ZRX_MAKER_FEE"],
        "takerFee": app.config["PYDEX_ZRX_TAKER_FEE"],
    }
    return json.dumps(res)

# GET FeeRecepients endpoint retrieves a collection of all fee recipient addresses for a relayer.
# http://sra-spec.s3-website-us-east-1.amazonaws.com/v2/fee_recipients
@app.route('/v2/fee_recipients', methods=["GET"])
def get_post_recipients():
    raise NotImplementedError()

# POST Order endpoint submits an order to the Relayer.
# http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/postOrder
@app.route('/v2/order', methods=["POST"])
@cross_origin()
def post_order():
    print("############ POSTING ORDER")
    print(request.json)
    order = SignedOrder.from_json(request.json, check_validity=True)
    db.session.add(order)
    db.session.commit()
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

# GET Order endpoint retrieves the order by order hash.
# http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrder
@app.route('/v2/order/', methods=["GET"])
def get_order_by_hash():
    raise NotImplementedError()
