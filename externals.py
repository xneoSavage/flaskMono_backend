from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_celeryext import FlaskCeleryExt

ext_celery = FlaskCeleryExt()
jwt = JWTManager()
db = SQLAlchemy()