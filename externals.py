from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import logging
from flask import request, jsonify

jwt = JWTManager()
db = SQLAlchemy()

def prev_month():
        now = datetime.now().date()
        prev_month_start = (now - timedelta(now.day-1)) - relativedelta(months=1)
        prev_month_end = prev_month_start + relativedelta(months=1)

        return prev_month_start, prev_month_end


def resource_log(func):
        def wrapper(*args, **kwargs):
                logging.info('Resource %s', request.method)
                logging.info('Resource %s', request.base_url)
                return func
        return jsonify(wrapper)


