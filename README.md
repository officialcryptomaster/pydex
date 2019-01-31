Introduction
=============
pydex is a python implementation of a 0x-based relayer focused on making it convenient to trade options markets from Augur. 


Setup Instructions
------------------

```
source setup
```

The above script will do two things:
1. It will fetch and install the `node_modules` required to run the [@0x-order-watcher](https://github.com/0xProject/0x-monorepo/tree/development/packages/order-watcher). 
2. It will create the pydex_env virtual environment and install the `python packages` required for running the DEX. 

The first time you run setup, you will also have to manually create the database. run python3 from the `src` directory, create and instance of the app, and create all tables using the following:
```
cd src
python3
>>> from pydex_app import db
>>> db.create_all()
```

Run Instructions
----------------
Run using script 

```
./run-pydex
```

The above script will do three things:

1. It will make sure the node and python dependencies are installed
2. It will ensure the order-watcher server is running
3. It will launch an instance of the pydex app at `localhost:3000`.