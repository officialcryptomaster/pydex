from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pydex_app.config as pydex_config

app = Flask(__name__)
app.config.from_object(pydex_config.PydexBaseConfig)

db = SQLAlchemy(app)

from pydex_app import routes