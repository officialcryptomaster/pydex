"""
Flask API routes

author: officialcryptomaster@gmail.com
"""
import json

from flask import request, render_template
from flask_cors import cross_origin
from zero_ex.json_schemas import assert_valid
from pydex_app import app, db  # pylint: disable=cyclic-import
from pydex_app.db_models import SignedOrder  # pylint: disable=cyclic-import
from pydex_app.orderbook import Orderbook  # pylint: disable=cyclic-import
from pydex_app.constants import NULL_ADDRESS


@app.route("/")
def hello():
    """Default route path with link to documentation."""
    app.logger.info("hello")
    return render_template("base.html")


@app.route("/v2/asset_pairs", methods=["GET"])
@cross_origin()
def get_asset_pairs():
    """GET AssetPairs endpoint retrieves a list of available asset pairs and the
    information required to trade them.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getAssetPairs
    """
    app.logger.error("not implemented")
    raise NotImplementedError()


@app.route("/v2/orders", methods=["GET"])
def get_orders():
    """GET Orders endpoint retrieves a list of orders given query parameters.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrders
    """
    app.logger.error("not implemented")
    raise NotImplementedError()


@app.route('/v2/orderbook', methods=["GET"])
@cross_origin()
def get_order_book():
    """GET Orders endpoint retrieves a list of orders given query parameters.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrders
    """
    app.logger.info("############ GETTING ORDER BOOK")
    network_id = request.args.get("networkId", app.config["PYDEX_NETWORK_ID"])
    assert network_id == app.config["PYDEX_NETWORK_ID"], \
        f"networkId={network_id} not supported"
    page = int(request.args.get("page", app.config["OB_DEFAULT_PAGE"]))
    per_page = int(request.args.get(
        "per_page", app.config["OB_DEFAULT_PER_PAGE"]))
    base_asset = request.args["baseAssetData"]
    quote_asset = request.args["quoteAssetData"]
    full_asset_set = request.args.get("fullSetAssetData")
    if full_asset_set:
        full_asset_set = json.loads(full_asset_set)
    bids, tot_bid_count = Orderbook.get_bids(
        base_asset=base_asset,
        quote_asset=quote_asset,
        full_asset_set=full_asset_set,
        page=page,
        per_page=per_page)
    asks, tot_ask_count = Orderbook.get_asks(
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


@app.route('/v2/order_config', methods=["POST"])
@cross_origin()
def post_order_config():
    """POST Order config endpoint retrives the values for order fields that the
    relayer requires.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrderConfig
    """
    app.logger.info("############ GETTING ORDER CONFIG")
    network_id = request.args.get("networkId", app.config["PYDEX_NETWORK_ID"])
    assert network_id == app.config["PYDEX_NETWORK_ID"], f"networkId={network_id} not supported"
    order = request.json
    assert_valid(order, "/orderConfigRequestSchema")
    res = {
        "senderAddress": NULL_ADDRESS,
        "feeRecipientAddress": app.config["PYDEX_ZRX_FEE_RECIPIENT"],
        "makerFee": app.config["PYDEX_ZRX_MAKER_FEE"],
        "takerFee": app.config["PYDEX_ZRX_TAKER_FEE"],
    }
    return json.dumps(res)


@app.route('/v2/fee_recipients', methods=["GET"])
def get_post_recipients():
    """GET FeeRecepients endpoint retrieves a collection of all fee recipient
    addresses for a relayer.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/v2/fee_recipients
    """
    app.logger.error("not implemented")
    raise NotImplementedError()


@app.route('/v2/order', methods=["POST"])
@cross_origin()
def post_order():
    """POST Order endpoint submits an order to the Relayer.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/postOrder
    """
    app.logger.info("############ POSTING ORDER")
    app.logger.info(request.json)
    order = SignedOrder.from_json(request.json, check_validity=True)
    db.session.add(order)  # pylint: disable=no-member
    db.session.commit()  # pylint: disable=no-member
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route('/v2/order/', methods=["GET"])
def get_order_by_hash():
    """GET Order endpoint retrieves the order by order hash.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrder
    """
    app.logger.error("not implemented")
    raise NotImplementedError()
