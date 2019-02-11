"""
Instance of pydex database kept separately to avoid circular import

author: officialcryptomaster@gmail.com
"""

from flask_sqlalchemy import SQLAlchemy

PYDEX_DB = SQLAlchemy()
