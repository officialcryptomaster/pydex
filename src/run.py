from pydex_app import app, db
from pydex_app.utils import setup_logger

# You can start the service as a Docker image
# docker run -ti -p 8080:8080 -e JSON_RPC_URL=https://mainnet.infura.io -e NETWORK_ID=1 0xorg/order-watcher
# or build the source and run node lib/src/server.js.
# test with wscat -c ws://0.0.0.0:8080

if __name__ == "__main__":
    db.create_all()
    
    l = setup_logger("app","app.log")
    app.logger = l
    app.logger.info("startup pydex")

    app.run(host="0.0.0.0", port=3000, debug=True)

