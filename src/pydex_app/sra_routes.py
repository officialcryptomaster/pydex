"""
Flask API routes

author: officialcryptomaster@gmail.com
"""
import json

from flask import request, render_template, Blueprint, current_app
from flask_cors import cross_origin
from zero_ex.contract_addresses import NetworkId
from zero_ex.json_schemas import assert_valid
from pydex_app.orderbook import Orderbook
from utils.web3utils import NULL_ADDRESS

sra = Blueprint("sra", __name__)  # pylint: disable=invalid-name


@sra.route("/")
def hello():
    """Default route path with link to documentation."""
    current_app.logger.info("hello")
    return render_template("base.html")


@sra.route("/v2/asset_pairs", methods=["GET"])
@cross_origin()
def get_asset_pairs():
    """GET AssetPairs endpoint retrieves a list of available asset pairs and the
    information required to trade them.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getAssetPairs
    """
    current_app.logger.info("############ GETTING ASSET PAIRS")
    network_id = NetworkId(int(request.args.get("networkId"))).value
    assert network_id == current_app.config["PYDEX_NETWORK_ID"], \
        f"networkId={network_id} not supported"
    page = int(request.args.get("page", current_app.config["OB_DEFAULT_PAGE"]))
    per_page = int(request.args.get(
        "per_page", current_app.config["OB_DEFAULT_PER_PAGE"]))
    asset_data_a = request.args.get("assetDataA")
    asset_data_b = request.args.get("assetDataB")
    include_maybe_fillables = bool(request.args.get("include_maybe_fillables"))
    asset_pairs, asset_pairs_count = Orderbook.get_asset_pairs(
        asset_data_a=asset_data_a,
        asset_data_b=asset_data_b,
        page=page,
        per_page=per_page,
        include_maybe_fillables=include_maybe_fillables
    )
    res = {
        "total": asset_pairs_count,
        "perPage": per_page,
        "page": page,
        "records": asset_pairs
    }
    assert_valid(res, "/relayerApiAssetDataPairsResponseSchema")
    return current_app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype='application/json'
    )


@sra.route("/v2/orders", methods=["GET"])
@cross_origin()
def get_orders():
    """GET Orders endpoint retrieves a list of orders given query parameters.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrders
    """
    current_app.logger.info("############ GETTING ORDERS")
    network_id = NetworkId(int(request.args.get("networkId"))).value
    assert network_id == current_app.config["PYDEX_NETWORK_ID"], \
        f"networkId={network_id} not supported"
    page = int(request.args.get("page", current_app.config["OB_DEFAULT_PAGE"]))
    per_page = int(request.args.get(
        "per_page", current_app.config["OB_DEFAULT_PER_PAGE"]))
    orders, orders_count = Orderbook.get_orders(
        maker_asset_proxy_id=request.args.get("makerAssetProxyId"),
        taker_asset_proxy_id=request.args.get("takerAssetProxyId"),
        maker_asset_address=request.args.get("makerAssetAddress"),
        taker_asset_address=request.args.get("takerAssetAddress"),
        exchange_address=request.args.get("exchangeAddress"),
        sender_address=request.args.get("takerAssetAddress"),
        maker_asset_data=request.args.get("makerAssetData") or request.args.get(
            "traderAssetData"),
        taker_asset_data=request.args.get("takerAssetData") or request.args.get(
            "traderAssetData"),
        maker_address=request.args.get("makerAddress") or request.args.get("traderAddress"),
        taker_address=request.args.get("takerAddress") or request.args.get("traderAddress"),
        fee_recipient_address=request.args.get("feeRecipient"),
        page=page,
        per_page=per_page,
        include_maybe_fillables=bool(request.args.get("include_maybe_fillables"))
    )
    res = {
        "total": orders_count,
        "perPage": per_page,
        "page": page,
        "records": orders
    }
    assert_valid(res, "/relayerApiOrdersResponseSchema")
    return current_app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype='application/json'
    )


@sra.route('/v2/orderbook', methods=["GET"])
@cross_origin()
def get_order_book():
    """GET Orders endpoint retrieves a list of orders given query parameters.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrders
    """
    current_app.logger.info("############ GETTING ORDER BOOK")
    network_id = NetworkId(int(request.args.get("networkId"))).value
    assert network_id == current_app.config["PYDEX_NETWORK_ID"], \
        f"networkId={network_id} not supported"
    page = int(request.args.get("page", current_app.config["OB_DEFAULT_PAGE"]))
    per_page = int(request.args.get(
        "per_page", current_app.config["OB_DEFAULT_PER_PAGE"]))
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
        per_page=per_page,
    )
    asks, tot_ask_count = Orderbook.get_asks(
        base_asset=base_asset,
        quote_asset=quote_asset,
        full_asset_set=full_asset_set,
        page=page,
        per_page=per_page,
    )
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
    # assert_valid(res, "/relayerApiOrderbookResponseSchema")
    return current_app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype='application/json'
    )


@sra.route('/v2/order_config', methods=["POST"])
@cross_origin()
def post_order_config():
    """POST Order config endpoint retrives the values for order fields that the
    relayer requires.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrderConfig
    """
    current_app.logger.info("############ GETTING ORDER CONFIG")
    network_id = request.args.get("networkId", current_app.config["PYDEX_NETWORK_ID"])
    assert network_id == current_app.config["PYDEX_NETWORK_ID"], f"networkId={network_id} not supported"
    order = request.json
    assert_valid(order, "/orderConfigRequestSchema")
    res = {
        "senderAddress": NULL_ADDRESS,
        "feeRecipientAddress": current_app.config["PYDEX_ZX_FEE_RECIPIENT"],
        "makerFee": current_app.config["PYDEX_ZX_MAKER_FEE"],
        "takerFee": current_app.config["PYDEX_ZX_TAKER_FEE"],
    }
    # assert_valid(res, "/relayerApiOrderConfigResponseSchema")
    return current_app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype='application/json'
    )


@sra.route('/v2/fee_recipients', methods=["GET"])
@cross_origin()
def get_post_recipients():
    """GET FeeRecepients endpoint retrieves a collection of all fee recipient
    addresses for a relayer.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/v2/fee_recipients
    """
    current_app.logger.info("############ GETTING FEE RECIPIENTS")
    page = int(request.args.get("page", current_app.config["OB_DEFAULT_PAGE"]))
    per_page = int(request.args.get(
        "per_page", current_app.config["OB_DEFAULT_PER_PAGE"]))
    normalized_fee_recipient = current_app.config["PYDEX_ZX_FEE_RECIPIENT"].lower()
    fee_recipients = [normalized_fee_recipient]
    res = {
        "total": len(fee_recipients),
        "perPage": per_page,
        "page": page,
        "records": fee_recipients
    }
    assert_valid(res, "/relayerApiFeeRecipientsResponseSchema")
    return current_app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype='application/json'
    )


@sra.route('/v2/order', methods=["POST"])
@cross_origin()
def post_order():
    """POST Order endpoint submits an order to the Relayer.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/postOrder
    """
    current_app.logger.info("############ POSTING ORDER")
    network_id = request.args.get("networkId", current_app.config["PYDEX_NETWORK_ID"])
    assert network_id == current_app.config["PYDEX_NETWORK_ID"], f"networkId={network_id} not supported"
    current_app.logger.info(request.json)
    assert_valid(request.json, "/signedOrderSchema")
    Orderbook.add_order(order_json=request.json)
    return current_app.response_class(
        response={'success': True},
        status=200,
        mimetype='application/json'
    )


@sra.route('/v2/order/<order_hash>', methods=["GET"])
@cross_origin()
def get_order_by_hash(order_hash):
    """GET Order endpoint retrieves the order by order hash.
    http://sra-spec.s3-website-us-east-1.amazonaws.com/#operation/getOrder
    """
    current_app.logger.info("############ GETTING ORDER BY HASH")
    assert_valid(order_hash, "/orderHashSchema")
    network_id = request.args.get("networkId", current_app.config["PYDEX_NETWORK_ID"])
    assert network_id == current_app.config["PYDEX_NETWORK_ID"], f"networkId={network_id} not supported"
    res = Orderbook.get_order_by_hash(order_hash=order_hash)
    assert_valid(res, "/relayerApiOrderSchema")
    return current_app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype='application/json'
    )
