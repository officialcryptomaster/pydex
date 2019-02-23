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

from threading import Thread

import websocket

from utils.logutils import setup_logger

LOGGER = setup_logger(__name__)


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
        server_url="ws://127.0.0.1:8080",
        on_open=None,
        on_update=None,
        on_error=None,
        on_close=None,
        enable_trace=False,
    ):
        """
        Keyword arguments:
        server_url -- string url and port where order-watcher-server is running the
            json RPC service
        on_open -- function with no args for when the web socket connection is first
            established
        on_update -- function with `message` arg for when updates are sent from the server
        on_error -- function with `error` arg for an error occurs in the web socket
        on_close -- function with no arg for when web socket is closed down
        enable_trace -- boolean indicating whether the web socket should have
            verbose debug information (default: False)
        """
        self.server_url = server_url
        self.on_open = on_open
        self.on_update = on_update
        self.on_error = on_error
        self.on_close = on_close
        self.enable_trace = enable_trace
        self.websoc = websocket.WebSocketApp(
            url=self.server_url,
            on_open=lambda ws: self.on_open_router(),
            on_message=lambda ws, message: self.on_update_router(message),
            on_error=lambda ws, error: self.on_error_router(error),
            on_close=lambda ws: self.on_close_router(),
        )
        self._msg_id = 1
        self._th = None

    def run(self):
        """Run an instance of the order-watcher-client in a separate thread"""
        if self._th:
            LOGGER.info("Already running...")
            return self
        websocket.enableTrace(self.enable_trace)
        self._th = Thread(target=self.websoc.run_forever)
        LOGGER.debug(
            "Starting web socket client in thread %s...", self._th)
        self._th.start()
        return self

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

    def _rpc(self, method, params=None):
        """Remote Procedure Call handler"""
        msg_json = {
            "id": self._msg_id,
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            msg_json["params"] = params
        LOGGER.debug("sending... %s", msg_json)
        websoc = websocket.create_connection(self.server_url)
        websoc.send(json.dumps(msg_json))
        self._msg_id += 1
        LOGGER.debug("receiving...")
        res = websoc.recv()
        LOGGER.debug("received %s", res)
        if not isinstance(res, dict):
            try:
                res = json.loads(res)
            except (json.decoder.JSONDecodeError, TypeError):
                LOGGER.exception(
                    "Result of send was not valid json. original message was:\n{}\n")
        return res

    def get_stats(self):
        """Get number of orders being watched by the server"""
        return self._rpc(method="GET_STATS")

    def add_order(self, signed_order):
        """Add an order to the server's watch list

        Keyword arguments:
        signed_order -- dict of a signedOrder
        """
        return self._rpc(
            method="ADD_ORDER",
            params={"signedOrder": signed_order})

    def remove_order(self, order_hash):
        """Remove an order from the server's watch list

        Keyword arguments:
        order_hash -- string hex hash of signed order
        """
        return self._rpc(
            method="REMOVE_ORDER",
            params={"orderHash": order_hash})

    def on_open_router(self):
        """Logs an info message and routes it to self.on_open."""
        LOGGER.info("### websocket@%s opened ###", self.server_url)
        if self.on_open:
            return self.on_open()
        return None

    def on_update_router(self, message):
        """Logs an info message, converts to json and routes 'result' to self.on_message"""
        LOGGER.info("got message: %s", message)
        if self.on_update:
            try:
                message = json.loads(message)
                message = message["result"]
            except (json.decoder.JSONDecodeError, TypeError, KeyError):
                LOGGER.exception(
                    "Update message had invalid format. original message was:\n{}\n")
                return message
            try:
                return self.on_update(message)
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("on_update() failed to handle message=%s", message)
        return message

    def on_close_router(self):
        """Default on_close logs the fact that web socket was closed."""
        LOGGER.info("### websocket@%s closed ###", self.server_url)
        if self.on_close:
            return self.on_close()
        return None

    def on_error_router(self, error):
        """Default on_error, just logs the error message."""
        LOGGER.error("got error: %s", error)
        if self.on_error:
            try:
                error = json.loads(error)
                error = error["error"]
            except (json.decoder.JSONDecodeError, TypeError, KeyError):
                LOGGER.exception(
                    "Error message had invalid format. original message was:\n{}\n")
                return error
            try:
                return self.on_error(error)
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("on_error() failed to handle error=%s", error)
        return error


if __name__ == "__main__":
    import signal

    OWC = OrderWatcherClient()

    def signal_handler(_signal, _frame):
        """Handle Ctrl+C signal by telling OrderWatcherClient to stop running"""
        LOGGER.warning("Ctrl+C detected... Will Stop!")
        OWC.stop()

    signal.signal(signal.SIGINT, signal_handler)

    OWC.run().join()
