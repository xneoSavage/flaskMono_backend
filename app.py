from flask import Flask
from config import Config
from flask_migrate import Migrate
from flask_restful import Api
from flask_cors import CORS
import logging
from celery import Celery
from resources.account import LoadAccount
from resources.user import Login, CreateUser, Logout, ChangePassword, Apikey

from externals import db, jwt, ext_celery



app = Flask(__name__)
app.debug = True
CORS(app)

# Config
app.config.from_object(Config)
app.config['JWT_SECRET_KEY'] = 'secret_key'

# Redis
app.config.broker_url = 'redis://localhost:6379/0'
app.config.broker_transport_options = {'visibility_timeout': 3600}  # 1 hour.
app.config.result_backend = 'redis://localhost:6379/0'
app.config.result_backend_transport_options = {'master_name': "mymaster"}
app.config.result_backend_transport_options = {
    'retry_policy': {
       'timeout': 5.0
    }
}

# Celery

celery = Celery(
    __name__,
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0"
)


@celery.task
def add(x, y):
    return


migrate = Migrate(app, db)
# login = LoginManager(app)
# login.init_app(app)
ext_celery.init_app(app)
db.init_app(app)
jwt.init_app(app)
api = Api(app)


CORS(app, resources={r"/*": {"origins": "*"}})
logging.getLogger('flask_cors').level = logging.DEBUG

# Resources
api.add_resource(Login, '/login')
# api.add_resource(User, '/user')
api.add_resource(Logout, '/logout')
api.add_resource(ChangePassword, '/change-password')
api.add_resource(CreateUser, '/create-user')
api.add_resource(Apikey, '/api-key')
api.add_resource(LoadAccount, '/load-account')


if __name__ == '__main__':
	app.run(debug=True, host='192.168.1.47', port=81)
