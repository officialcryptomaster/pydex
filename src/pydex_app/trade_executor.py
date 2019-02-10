"""Web3.py"""
from web3 import Web3  # pylint: disable=invalid-name
from zero_ex.contract_artifacts import abi_by_name
from pydex_app import app


class TradeExecutor:
    """This class initalizes an instance of the zrx_exchange contract and executes trades """

    def __init__(self, address, private_key, rpc_url, exchange_address):
        # Fee recipient address and private key
        self._address = address
        self._private_key = private_key
        # Initialize chain_id
        self._chain_id = app.config["PYDEX_NETWORK_ID"]
        # Initialize web3
        self._web3 = Web3(
            Web3.HTTPProvider(
                rpc_url,
                request_kwargs={"timeout": 60}))
        self._web3_eth = self._web3.eth  # pylint: disable=no-member
        # Initalize zrx_exchange contract
        self.zrx_exchange = self._web3_eth.contract(
            address=exchange_address,
            abi=abi_by_name("exchange"))

    def execute_fill_or_kill(self, order, taker_asset_fill_amount, signatures):
        """Executes an array of signed_orders"""
        func_params = [order, taker_asset_fill_amount, signatures]
        function = self.zrx_exchange.functions.fillOrKillOrder(*func_params)
        tx_params = self._get_tx_params()
        return self._build_and_send_tx(function, tx_params)

    def execute_batch_fill_or_kill(self, orders, taker_asset_fill_amounts, signatures):
        """Executes a single signed_order"""
        func_params = [orders, taker_asset_fill_amounts, signatures]
        function = self.zrx_exchange.functions.batchFillOrKill(*func_params)
        tx_params = self._get_tx_params()
        return self._build_and_send_tx(function, tx_params)

    def _get_tx_params(self, value=0, gas=150000):
        """Get generic transcation parameters."""
        return {
            "chain_id": self._chain_id,
            "from": self._address,
            "value": value,
            "gas": gas,
            "nonce": self._web3_eth.getTransactionCount(self._address)
        }

    def _build_and_send_tx(self, function, tx_params):
        """Build and send a transaction to the zrx_exchange"""
        transaction = function.buildTransaction(tx_params)
        signed_tx = self._web3_eth.account.signTransaction(
            transaction, private_key=self._private_key)
        return self._web3_eth.sendRawTransaction(signed_tx.sendRawTransaction)
