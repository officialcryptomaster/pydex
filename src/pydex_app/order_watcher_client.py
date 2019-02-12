"""
OrderWatcherClient is the client responsible for registering orders with the
0x order-watcher server.

For this client to work, there needs to be an order-watcher server running.
The easiest way to run the server is using the `start-order-watcher` which is
provided with this project.
It is also possible to run the server as a Docker image using:
`docker run -ti -p 8080:8080 -e JSON_RPC_URL=https://mainnet.infura.io \\`
    `-e NETWORK_ID=1 0xorg/order-watcher`
You can test that the service is running with
`wscat -c ws://0.0.0.0:8080`

author: officialcryptomaster@gmail.com
"""

import json
import logging

from threading import Thread

import websocket

from pydex_app.utils import setup_logger

LOGGER = logging.getLogger(__name__)


class OrderWatcherClient:
    """OrderWatcherClient is for listening to order-watcher-server service.
    Currently, there is no equivalent of the 0x-order-watcher object in python.
    The typescript library does have a server which provides an RPC interface.
    This class is meant to be the client which registers orders with the server
    and listens to status updates. It has apprpriate hooks which can be used to
    perform orderbook updates.
    """

    def __init__(
        self,
        url="ws://127.0.0.1:8080",
        on_open=None,
        on_msg=None,
        on_error=None,
        on_close=None,
        enable_trace=False,
    ):
        """
        Keyword arguments:
        url -- string url and port where order-watcher-server is running the json
            RPC service
        on_open -- function hook for when the web socket connection is first
            established
        on_msg -- function hook for when updates are sent from the server
        on_error -- function hook for an error occurs in the web socket
        on_close -- function hook for when web socket is closed down
        enable_trace -- boolean indicating whether the web socket should have
            verbose debug information (default: False)
        """
        self.url = url
        self.on_open = on_open
        self.on_msg = on_msg
        self.on_error = on_error
        self.on_close = on_close
        self.enable_trace = enable_trace
        self.websoc = websocket.WebSocketApp(
            url=self.url,
            on_open=on_open,
            on_message=on_msg,
            on_error=on_error,
            on_close=on_close
        )
        self._msg_id = 1
        self._th = None

    def run(self):
        """Run an instance of the order-watcher-client in a separate thread
        """
        if self._th:
            LOGGER.info("Already running...")
            return
        websocket.enableTrace(self.enable_trace)
        self._th = Thread(target=self.websoc.run_forever)
        LOGGER.debug(
            "Starting web socket client in thread %s...", self._th)
        self._th.start()

    def stop(self):
        """Force the websocket to close and the background thread to stop"""
        self.websoc.close()
        self._th = None

    def join(self):
        """Wait for websocket
        Note that the background thread will run until you call `stop()` on
        the client.
        """
        if self._th:
            self._th.join()

    def on_open_default(self, *args, **kwargs):  # pylint: disable=unused-argument
        """Default on_open function just gets number of order being watched by
        the server.
        """
        LOGGER.info("### open ###")
        stats = self.get_stats()
        LOGGER.info("Got stats: %s", stats.get("result"))

    def _rpc(self, method, params=None, on_msg=None, on_error=None):
        """Remote Procedure Call handler
        """
        new_id = self._msg_id + 1
        msg_json = {
            "id": new_id,
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            msg_json["params"] = params
        LOGGER.debug("sending... %s", msg_json)
        websoc = websocket.create_connection(self.url)
        websoc.send(json.dumps(msg_json))
        self._msg_id = new_id + 1
        LOGGER.debug("receiving...")
        res = websoc.recv()
        LOGGER.debug("received %s", res)
        on_msg = on_msg or self.on_msg
        on_error = on_error or self.on_error
        if not isinstance(res, dict):
            try:
                res = json.loads(res)
            except (json.decoder.JSONDecodeError, TypeError):
                LOGGER.exception(
                    "Result of send was not valid json. original message was:\n{}\n")
                if on_error:
                    return on_error(res)
                return None
        if on_msg:
            return on_msg(res)
        return None

    def get_stats(self):
        """Get number of orders being watched by the server"""
        return self._rpc(method="GET_STATS")

    def add_order(self, signed_order):
        """Add an order to the server's watch list

        Keyword arguments:
        signed_order: dict of a signedOrder
        """
        self._rpc(
            method="ADD_ORDER",
            params={"signedOrder": signed_order})

    def remove_order(self, order_hash):
        """Remove an order from the server's watch list

        Keyword arguments:
        order_hash: string hex hash of signed order
        """
        self._rpc(
            method="REMOVE_ORDER",
            params={"orderHash": order_hash})


if __name__ == "__main__":

    LOGGER = setup_logger(__name__, file_name="order_watcher.log")

    order_watcher = OrderWatcherClient(  # pylint: disable=invalid-name
        on_msg=LOGGER.info,
        on_error=LOGGER.error,
    )
    order_watcher.run()
    order_watcher.join()
