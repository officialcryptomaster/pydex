from web3 import Web3
from zero_ex.contract_artifacts import abi_by_name;


class TradeExecutor:
    def __init__(self, address, private_key, rpc_url, chainId, exchange_address):
        # Fee recipient address and private key
        self.address = address
        self.private_key = private_key
        # Initialize web3
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60})
        # Initalize zrx_exchange contract
        self.zrx_exchange=self.w3.eth.contract(
            address=exchange_address, abi=abi_by_name("exchange"))
        # Initialize chainId
        self.chainId=chainId

    def execute_batch_fill_or_kill(self, orders, takerAssetFillAmounts, signatures):
        func_params=[orders, takerAssetFillAmounts, signatures];
        function=zrx_exchange.functions.batchFillOrKill(*func_params);
        return self._build_and_send_tx(function);


    def _get_tx_params(self, value=0, gas=150000):
        # Get generic transcation parameters.
        return {
            "chainId": self.chainId,
            "from": self.address,
            "value": value,
            "gas": gas,
            "nonce": self.w3.eth.getTransactionCount(self.address)
        }

    def _build_and_send_tx(function):
        # Build and send a transaction to the zrx_exchange
        tx_params=_get_tx_params();
        transaction=function.buildTransaction(tx_params);
        signed_tx=self.w3.eth.account.signTransaction(
            transaction, private_key=self.private_key);
        return self.w3.eth.sendRawTransaction(signed_tx.sendRawTransaction);
