import json
import logging
import logging.config
from datetime import datetime, timedelta

from flask import Flask, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

from config import Config
from externals import db, jwt
from resources.account import (
    AccountsData,
    LoadAccount,
)
from resources.transaction import (
    AllTransactions,
    AmountByMCC,
    CreditTransactions,
    LoadTransaction,
    TransByMCC,
    MccAmountMonth,
    TransStatisticDebitCredit,
)
from resources.user import (
    Apikey,
    ChangePassword,
    CreateUser,
    Login,
    Logout,
)




# init app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
CORS(app)

def configure_logging(app):
    """Configure logging for the given Flask application.

        Args:
            app: The Flask application object.

        This function configures logging for the application by setting the logger
        level to logging.INFO and adding a file handler that logs to a file named
        "logging.log". If the application is in debug mode, the logger level is
        set to logging.DEBUG and the logger for SQLAlchemy engine is also set to
        logging.INFO.
    """
    logging.getLogger().setLevel(logging.INFO)
    handler = logging.FileHandler('logging.log', mode='a',
                                  encoding='utf-8', delay=False)
    logging.getLogger().addHandler(handler)

    if app.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if app.debug:
        # Make sure engine.echo is set to False
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


# Config
configure_logging(app)
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('simpleExample')

app.config.from_object(Config)
app.config['JWT_SECRET_KEY'] = 'secret_key'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=24)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

app.wsgi_app = DispatcherMiddleware( # https://dlukes.github.io/flask-wsgi-url-prefix.html
    Response('Not Found', status=404),
    {'/api_v1': app.wsgi_app}
)

migrate = Migrate(app, db)
db.init_app(app)
jwt.init_app(app)
api = Api(app)
CORS(app)
@app.before_request
def before_request():
    """Log details of incoming request for debugging purposes.

      This hook is run before each request is processed. It logs various details
      about the incoming request, including the time, remote IP address, protocol,
      method, host, URL, path, query string, headers, query arguments, body
      arguments, and raw body data. If the content type of the request is
      "application/json", the hook also attempts to parse the body as JSON and
      log the resulting dictionary.
    """

    if not app.debug:
        return

    lines = []
    time_now = datetime.now()
    lines.append('Time: ' + time_now.strftime('%Y-%m-%d %H:%M:%S'))
    lines.append('Remote IP: ' + request.remote_addr)
    lines.append('Protocol: ' + str(request.scheme))
    lines.append('Method: ' + request.method)
    lines.append('Host: ' + request.host)
    lines.append('URL: ' + request.url)
    lines.append('Path: ' + request.path)
    lines.append('Query: ' + repr(request.query_string))

    header_texts = [
        '{0}: {1}'.format(repr(x[0]), repr(x[1]))\
        for x in request.headers
    ]

    lines.append('Headers:\n```\n{0}\n```'.format('\n'.join(header_texts)))
    lines.append('Query arguments:')
    query_arguments = dict(request.args)

    lines.append(
        json.dumps(
            query_arguments, ensure_ascii=False, indent=4, sort_keys=True,
        )
    )

    lines.append('Body arguments:')
    body_arguments = dict(request.form)

    lines.append(
        json.dumps(
            body_arguments, ensure_ascii=False, indent=4, sort_keys=True,
        )
    )

    body_data = request.environ.get('raw_body')

    if body_data is None:
        body_data = request.get_data()

    lines.append('Body: {0}'.format(repr(body_data)))

    if body_data:
        content_type = request.headers.get('Content-Type')

        if content_type == 'application/json':
            try:
                body_dict = json.loads(request.data.decode('utf-8'))

                body_text = json.dumps(
                    body_dict, ensure_ascii=False, indent=4, sort_keys=True,
                )

                lines.append('Body dict:\n{0}'.format(body_text))
            except Exception:
                pass

    message = '\n# ----- Request -----\n{0}\n'.format(
        '\n'.join(lines),
    )
    lines.append('SQL:' + 'sqlalchemy.engine')
    logging.debug(message)


@app.after_request
def after_request(response):
    """Log details of outgoing response for debugging purposes.

        This hook is run after each request is processed. It logs various details
        about the response that was generated for the request, including the time,
        path, status code, headers, and body data. If the content type of the
        response is "application/json", the hook also attempts to parse the body
        as JSON and log the resulting dictionary.
    """
    if not app.debug:
        return response

    lines = []
    time_now = datetime.now()
    lines.append('Time: ' + time_now.strftime('%Y-%m-%d %H:%M:%S'))
    lines.append('Path: ' + request.path)
    lines.append('Status: {0}'.format(response.status))
    header_texts = [
        '{0}: {1}'.format(repr(x[0]), repr(x[1]))\
        for x in response.headers
    ]
    lines.append('Headers:\n```\n{0}\n```'.format('\n'.join(header_texts)))
    try:
        body = response.get_data()
    except Exception:
        body = None


    content_type = response.headers.get('Content-Type')
    if content_type == 'application/json':
        try:
            body_dict = json.loads(body)
            body_text = json.dumps(
                body_dict, ensure_ascii=False, indent=4, sort_keys=True,
            )

            lines.append('Body dict:\n{0}'.format(body_text[-300:-1]))
        except Exception:
            pass

    message = '\n# ----- Response -----\n{0}\n'.format(
        '\n'.join(lines),
    )
    logging.debug(message)

    return response




# Resources
api.add_resource(Login, '/login')
# api.add_resource(User, '/user')
api.add_resource(Logout, '/logout')
api.add_resource(ChangePassword, '/change-password')
api.add_resource(CreateUser, '/create-user')
api.add_resource(Apikey, '/api-key')
api.add_resource(LoadAccount, '/load-account')
api.add_resource(AccountsData, '/get-account')
api.add_resource(LoadTransaction, '/load-transaction')
api.add_resource(AllTransactions, '/get-transaction')
api.add_resource(CreditTransactions, '/credit-transaction')
api.add_resource(TransStatisticDebitCredit, '/trans-debit-credit')
api.add_resource(AmountByMCC, '/amount-mcc')
api.add_resource(TransByMCC, '/trans-mcc')
api.add_resource(MccAmountMonth, '/mcc-month')

if __name__ == '__main__':
    app.run(host='127.0.0.47', port='81', debug=True, use_debugger=True)
