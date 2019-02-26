Introduction
=============
PyDEX is a python-based DEX (decentralized exchange) which makes use of the [0x Protocol](https://0x.org/). The initial goal of this project is to deliver an out-of-the-box python implementation of the [Standard Relayer API](https://github.com/0xProject/standard-relayer-api) which utilizes the [open orderbook relayer model](https://0x.org/wiki#Open-Orderbook), much like the typescript-based [0x-launch-kit](https://github.com/0xproject/0x-launch-kit) provided by the 0x team. However, we do plan to extend this beyond just open orderbook model to a more sophisticated [matching relayer model](https://0x.org/wiki#Matching) and this would take us beyond the SRA into a custom API which is yet to be designed.

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


Development 
-----------
### Note on Contribution
While contribution to this project is highly encouraged and appreciated, I would greatly appreciate any PRs to fully adhere to the following guidelines:

1. Make sure all tests pass
```
PYTHONPATH=./src ./pydex_env/bin/pytest
```

2. Make sure `pylint` and `flake8` do not show any issues by running:
```
PYTHONPATH=./src ./pydex_env/bin/pylint src tests
PYTHONPATH=./src ./pydex_env/bin/flake8 src tests
```

Hint: you can greatly reduce linting problems by making use of `autopep8` which is installed as part of the dev requirements and is configured to run every time you save a file in the visual studio settings provided with this project (`.vscode/settings.json`)

3. Please ensure your PR is rebased to master branch with interactive merging which squashes any useless intermediate commits. The commit comments must use imperative tense and be clear and concise.


### Setting up Development Environment
First make sure the environment is active
```
source pydex_env/bin/activate
```
Then, install all the dev requirements:
```
pip3 install -r dev_requirements.txt
```


### Note on using jupyter notebooks to interactively play around with pyDEX
As always, make sure the environment is active (`source pydex_env/bin/activate`). Then, run juputer from the ./notebooks directory using the command:
```
PYTHONPATH=../src jupyter notebook
```