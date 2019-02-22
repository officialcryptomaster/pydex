"""
Use an OrderWatcherClient to listen to order updates from
the order-watcher-server and take necessary actions to ensure
order statuses are kept up to date in the database

author: officialcryptomaster@gmail.com
"""
from time import sleep
from pydex_app.database import PYDEX_DB as db
from pydex_app.db_models import SignedOrder, OrderStatus
from pydex_app.order_watcher_client import OrderWatcherClient
from utils.logutils import setup_logger
from utils.miscutils import now_epoch_msecs


LOGGER = setup_logger(__name__)


class OrderUpdateHandler:
    """Class for keeping SignedOrder statuses up-to-date.

    When orders are initially submitted and entered into the database, they will have
    order_status OrderStatus.MAYBE_FILLABLE and will not be displayed in the orderbook
    since the orderbook only displays FILLABLE orders. The OrderUpdateHandler is reponsible
    for fetching these orders from the database, registering them with the order watcher
    server and only then mark them as fillable. It will also listen to the order watcher
    server for updates on order statuses and update them as needed.
    Internally will make use of the OrderWatcherClient which will run and handle status
    updates on a separate thread.
    """

    def __init__(
        self,
        app,
        order_watcher_server_url="ws://127.0.0.1:8080",
        db_check_period_secs=1,
        heatbeat_period=30,
    ):
        """Get an instance of the OrderUpdateHandler.

        Keyword arguments:
        app -- PyDEX flask app instance, so we can make sure the context for database
            operations can be controlled
        server_url -- string url and port where order-watcher-server is running the
            json RPC service
        db_check_period_secs -- integer seconds between checking db for new orders
        heatbeat_period_secs -- integers number of db_check_period_secs betweeen logging a
            debug message (default: 30)
        """
        self._app = app
        self.db_check_period_secs = db_check_period_secs
        self.heartbeat_period_secs = heatbeat_period
        self._last_db_check_at = None
        self._last_update_at = None
        self.running = False
        # For now, all unfillable handlers will just mark the order as unfillable,
        # but you can potentially change this if you desire...
        self.unfillable_handlers = {
            "ORDER_FILL_EXPIRED": self.handle_unfillable_order,
            "ORDER_ALREADY_CANCELLED_OR_FILLED": self.handle_unfillable_order,
            "ORDER_REMAINING_FILL_AMOUNT_ZERO": self.handle_unfillable_order,
            "ORDER_FILL_ROUNDING_ERROR": self.handle_unfillable_order,
            "FILL_BALANCE_ALLOWANCE_ERROR": self.handle_unfillable_order,
            "INSUFFICIENT_TAKER_BALANCE": self.handle_unfillable_order,
            "INSUFFICIENT_TAKER_ALLOWANCE": self.handle_unfillable_order,
            "INSUFFICIENT_MAKER_BALANCE": self.handle_unfillable_order,
            "INSUFFICIENT_MAKER_ALLOWANCE": self.handle_unfillable_order,
            "TRANSACTION_SENDER_IS_NOT_FILL_ORDER_TAKER": self.handle_unfillable_order,
            "INSUFFICIENT_REMAINING_FILL_AMOUNT": self.handle_unfillable_order,
        }
        self.owc = OrderWatcherClient(
            server_url=order_watcher_server_url,
            on_update=self.on_update,
        )

    def _fetch_non_unfillables(self):
        """Fetch dict of orders which are not unfillable and have had updates"""
        fillables = {}
        maybe_fillables = {}
        filter_cond = SignedOrder.order_status >= 0
        if self._last_update_at:
            filter_cond &= SignedOrder.last_updated_at > self._last_update_at
        self._last_db_check_at = now_epoch_msecs()
        non_unfillables = {o.hash: o for o in
                           SignedOrder.query.filter(filter_cond)}
        if non_unfillables:
            self._last_update_at = max(
                [o.last_updated_at for o in non_unfillables.values()])
            LOGGER.info("fetched %s non-unfillable orders", len(non_unfillables))
            fillables = {h: o for h, o in non_unfillables.items() if o.order_status > 0}
            maybe_fillables = {h: o for h, o in non_unfillables.items() if o.order_status == 0}
        return fillables, maybe_fillables

    def run(self):
        """Infinite loop of the updater"""
        self.owc.run()
        self.running = True
        i = 1
        with self._app.app_context():
            LOGGER.info("starting main loop....")
            while self.running:
                i += 1
                if i % self.heartbeat_period_secs == 0:
                    LOGGER.debug(".")
                if self._last_db_check_at:
                    wait_secs = (self.db_check_period_secs
                                 - (now_epoch_msecs()
                                    - self._last_db_check_at) / 1000)
                    if wait_secs > 0:
                        sleep(wait_secs)
                fillables, maybe_fillables = self._fetch_non_unfillables()
                if fillables:  # force update from order-watcher-server
                    for order in fillables.values():
                        self.owc.add_order(order.to_json())
                if maybe_fillables:
                    for order in maybe_fillables.values():
                        self.handle_maybe_fillable_order(order=order, commit=False)
                    self._commit_db()
        LOGGER.info("main loop stopped!")
        LOGGER.info("stopping OrderWacherClient...")
        self.owc.stop()

    def on_update(self, res):
        """Handle messages coming from order-watcher-server.
        Note that this will be running in the order-watcher-client thread, so
        we need to make sure it operates within the app_context.

        Keyword argument:
        res -- dict 'result' from order-watcher-server on_message callback
        """
        LOGGER.info("handling update=%s", res)
        order_hash = res.get("orderHash")
        if order_hash is None:
            LOGGER.error("result missing 'orderHash' key")
            return res
        is_valid = res.get("isValid")
        if is_valid is None:
            LOGGER.error("result is missing 'isValid' key")
            return res
        # Since, handler is running in order-watcher-client thread,
        # it will need to be told about the app context
        with self._app.app_context():
            if not is_valid:
                invalid_reason = res.get("error")
                self.unfillable_handlers[invalid_reason](
                    order_hash, invalid_reason)
            else:
                LOGGER.info("Got valid order %s", order_hash)
                self.handle_fillable_order(order_hash)
        return res

    def get_order_by_hash(self, order_hash):
        """Get an order by hash from the database.

        Keyword argument:
        order_hash -- string hex hash of order
        """
        order = SignedOrder.query.get(order_hash)
        if not order:
            LOGGER.warning("Got update for ghost order with hash %s", order_hash)
        return order

    def handle_maybe_fillable_order(self, order, commit=True):
        """Add the order to the order-watcher-server and set it to FILLABLE.

        Keyword arguments:
        order_hash -- string hex hash of order
        commit -- boolean of whether to commit the change (default: True)
        """
        LOGGER.debug("Adding order_hash=%s to order-watcher-server", order.hash)
        # WARNING: this approach may be vulnerable to a race conditions, however,
        # since the order watcher server does not confirm valid status, it is the
        # simplest way we can mark a MAYBE_FILLABLE as FILLABLE...
        order_count_before = self.owc.get_stats()["result"]["orderCount"]
        self.owc.add_order(order.to_json())
        order_count_after = self.owc.get_stats()["result"]["orderCount"]
        if order_count_after > order_count_before:
            order.order_status = OrderStatus.FILLABLE.value
            if commit:
                self._commit_db()

    def handle_fillable_order(self, order_hash, commit=True):
        """Handle fillable order update.

        Keyword argument:
        order_hash -- string hex hash of order
        commit -- boolean of whether to commit the change (default: True)
        """
        LOGGER.debug("order with hash=%s is fillable", order_hash)
        order = self.get_order_by_hash(order_hash)
        if order:
            order.order_status = OrderStatus.FILLABLE.value
            if commit:
                self._commit_db()

    def handle_unfillable_order(
        self,
        order_hash,
        reason,
        commit=True,
    ):
        """Handle unfillable order update by marking it as unfillable

        Keyword argument:
        order_hash -- string hex hash of order
        reason -- string error code. This is the 'error' key from inside
            order-watcher-server's on_message 'result' key and must match
            one of the keys from self.unfillable_handlers.
        commit -- boolean of whether to commit the change (default: True)
        """
        LOGGER.debug("Setting order_hash=%s to NOT_FILLABLE due to %s",
                     order_hash, reason)
        order = self.get_order_by_hash(order_hash)
        if order:
            order.order_status = OrderStatus.UNFILLABLE.value
            if commit:
                self._commit_db()

    def _commit_db(self):
        LOGGER.debug("commit changes to DB...")
        db.session.commit()  # pylint: disable=no-member


if __name__ == "__main__":
    import signal
    from pydex_app import create_app  # pylint: disable=ungrouped-imports

    APP = create_app()

    OSU = OrderUpdateHandler(app=APP)

    def signal_handler(_signal, _frame):
        """Handle Ctrl+C signal by telling OrderStatusUpdate to stop running"""
        LOGGER.warning("Ctrl+C detected... Will Stop!")
        OSU.running = False
        OSU.owc.stop()

    signal.signal(signal.SIGINT, signal_handler)

    OSU.run()
