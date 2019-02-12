"""
Run an instance of the pyDEX App

author: officialcryptomaster@gmail.com
"""

from pydex_app import create_app


if __name__ == "__main__":
    APP = create_app()
    APP.logger.info("starting pydex...")
    APP.run(host="0.0.0.0", port=3000, debug=True)
