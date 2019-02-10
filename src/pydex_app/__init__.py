"""
pyDEX module

author: officialcryptomaster@gmail.com
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pydex_app.config as pydex_config

app = Flask(__name__)  # pylint: disable=invalid-name
app.config.from_object(pydex_config.PydexBaseConfig)

db = SQLAlchemy(app)  # pylint: disable=invalid-name

# This import needs to be here for routes to work... it confuses linters
from pydex_app import routes  # noqa: F401 pylint: disable=wrong-import-position
