from flask import Flask
from config import Config
from flask_migrate import Migrate
from flask_restful import Api
from flask_cors import CORS
import logging

from resources.user import Login, CreateUser, User, Logout, ChangePassword
from externals import db, jwt



app = Flask(__name__)
app.debug = True
CORS(app)

# Config
app.config.from_object(Config)
app.config['JWT_SECRET_KEY'] = 'secret_key'
migrate = Migrate(app, db)
# login = LoginManager(app)
# login.init_app(app)

db.init_app(app)
jwt.init_app(app)
api = Api(app)


CORS(app, resources={r"/*": {"origins": "*"}})
logging.getLogger('flask_cors').level = logging.DEBUG

# Resources
api.add_resource(Login, '/login')
api.add_resource(User, '/user')
api.add_resource(Logout, '/logout')
api.add_resource(ChangePassword, '/change-password')
api.add_resource(CreateUser, '/create-user')


if __name__ == '__main__':
	app.run(debug=True, host='192.168.1.47', port=81)
