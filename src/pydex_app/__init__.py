"""
pyDEX module

author: officialcryptomaster@gmail.com
"""

from flask import Flask

from pydex_app.database import PYDEX_DB as db
import pydex_app.config as pydex_config
from pydex_app.utils import setup_logger


def create_app(config=pydex_config.PydexBaseConfig):
    """Create and instance of the the pyDEX app from config"""
    # create an instance of the app
    app = Flask(__name__)
    # configure the app from the config
    app.config.from_object(config)
    # override the logger to write to command line and file
    app.logger = setup_logger("pyDEX_app", "pydex_app.log")

    # configure the database with the app
    db.init_app(app)

    # The following is a hack to make sure the DB is created on init
    with app.app_context():
        # IMPORTANT: need to import all DB models one by one
        from pydex_app.db_models import SignedOrder  # noqa: F401 pylint: disable=unused-import
        db.create_all()

    # import all blueprints and register them with the app
    from pydex_app.sra_routes import sra
    app.register_blueprint(sra)

    return app
