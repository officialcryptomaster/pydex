import time
import websocket
import json
import logging
from threading import Thread

logger = logging.getLogger(__name__)


class OrderWatcherClient:

    def __init__(
        self,
        url="ws://127.0.0.1:8080",
        on_open=None,
        on_msg=None,
        on_error=None,
        on_close=None,
        enable_trace=False,
    ):
        self.url = url
        self.on_open = on_open or self.on_open_default
        self.on_msg = on_msg or self.on_msg_default
        self.on_error = on_error or self.on_error_default
        self.on_close = on_close or self.on_close_default
        self.on_open = on_open or self.on_open_default
        self.enable_trace = enable_trace
        self.ws = websocket.WebSocketApp(
            url=self.url,
            on_open=self.on_open,
            on_message=on_msg,
            on_error=on_error,
            on_close=on_close
        )
        self._msg_id = 1
        self._th = None

    def run(self):
        if self._th:
            logger.info("Already running...")
            return
        websocket.enableTrace(self.enable_trace)
        self._th = Thread(target=self.ws.run_forever)
        logger.debug(
            "Starting web socket client in thread {}...".format(self._th))
        self._th.start()

    def stop(self):
        self.ws.close()
        self._th = None

    def join(self):
        if self._th:
            self._th.join()

    def get_stats(self):
        return self._rpc(method="GET_STATS")

    def on_open_default(self, *args, **kwargs):
        logger.info("### open ###")
        stats = self.get_stats()
        logger.info("Got stats: {}".format(stats.get("result")))

    def on_msg_default(self, msg):
        if not isinstance(msg, dict):
            try:
                msg = json.loads(msg)
            except Exception:
                logger.exception(
                    "Error in parsing message. Expected valid json, but got:\n{}\n".format(msg))
                return
        res = msg.get("result")
        if not res:
            logger.error(
                "Error in rpc message... missing 'result' key... {}".format(msg))
            return
        # TODO: handle the different message types
        logger.info(msg)
        return msg

    def on_error_default(self, ws, error):
        logger.error(error)

    def on_close_default(self, ws):
        logger.info("### closed ###")

    def _rpc(self, method, params=None, on_msg=None, on_err=None):
        new_id = self._msg_id + 1
        msg_json = {
            "id": new_id,
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            msg_json["params"] = params
        logger.debug("sending... {}".format(msg_json))
        ws = websocket.create_connection(self.url)
        ws.send(json.dumps(msg_json))
        self._msg_id = new_id + 1
        logger.debug("receiving...")
        res = ws.recv()
        logger.debug("received {}".format(res))
        if not isinstance(res, dict):
            try:
                res = json.loads(res)
            except Exception:
                logger.exception(
                    "Result of send was not valid json. original message was:\n{}\n")
                self.on_error(res)
                return
        on_msg = on_msg or self.on_msg
        return self.on_msg(res)

    def add_order(self, order_hash):
        pass


if __name__ == "__main__":
    # create console handler and set level to debug
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d - %(funcName)20s() - %(levelname)s - %(message)s",
        "%m-%d %H:%M:%S")
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    order_watcher = OrderWatcherClient()
    order_watcher.run()
    order_watcher.join()
