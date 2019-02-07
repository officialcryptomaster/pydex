Introduction
=============
PyDEX is a python-based DEX which makes use of the 0x protocol.

Setup Instructions
------------------
Make sure you have python3 and virtualenv installed. On Mac OS you can use [brew](https://brew.sh/) to install python3 and then pip3 to install virtualenv
```
brew install python3
pip3 install virtualenv
```
Once you have confirmed python3 and virtual env are successfully installed, install all the dependencies using:
```
source setup
```

The above script will do three things:
1. It will fetch and install the `node_modules` required to run the [@0x-order-watcher](https://github.com/0xProject/0x-monorepo/tree/development/packages/order-watcher). 
2. It will create the `pydex_env` virtual environment and install the python packages required for running PyDEX.
3. It will activate the virtualenv required for running pydex


Run Instructions
----------------
Run using script 

```
source run-pydex
```

The above script will do three things:

1. It will make sure the node and python dependencies are installed (by calling `source setup`)
2. It will ensure the order-watcher server is running
3. It will launch an instance of the pydex app at `localhost:3000`.

Optionally you can set the following environment variables:

* `NETWORK_ID`: integer ID of network (`1`: MainNet, `4`: Rinkeby, `42`: Kovan, `50`: Ganache)
* `JSON_RPC_URL`: URL to your Web3 provider to be used by **order-watcher-server**. (Either a local ethereum node, or a public one like [Infura](https://infura.io) which typically will look like `https://rinkeby.infura.io/<your API key here>`). If you do not set this, it will default to the local Ganache URI at `http://localhost:8545`.
* `PRIVATE_KEY`: your private key as a hex string to be used for executing orders on the relayer's behalf. Note that this is currently not secure so do not use for mainnet deployment.