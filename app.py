from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
#from flask_login import LoginManager, current_user
from flask_restful import Api, Resource
from flask_cors import CORS
import logging
import os

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager




app = Flask(__name__)
app.debug = True
CORS(app)

# Config
app.config.from_object(Config)
app.config['JWT_SECRET_KEY'] = 'secret_key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
#login = LoginManager(app)
#login.init_app(app)
jwt = JWTManager(app)
api = Api(app)
CORS(app, resources={r"/*": {"origins": "*"}})
logging.getLogger('flask_cors').level = logging.DEBUG


from resources.example import User, Login, Logout, CreateUser
api.add_resource(User, '/')
api.add_resource(CreateUser, '/createUser')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
from logging.config import dictConfig

#logging.basicConfig(filename='demo.log', level=logging.DEBUG)


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=80)