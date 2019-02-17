FROM python:3.6

RUN apt-get update && apt-get install -y libssl-dev

COPY dev_requirements.txt ./
RUN pip3 install -r dev_requirements.txt

COPY . ./pydex/

WORKDIR ./pydex

RUN PYTHONPATH=./src pytest
# assert _web3_rpc_url, "Please make sure a WEB3_RPC_URL is set"
