import os

import app

basedir = os.path.abspath(__file__)

class Config(object):
	SECRET_KEY = 'SECRET_KEY'
	MONOBANK_TOKEN = os.environ.get('MONO_TOKEN')
	# db connection
	SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:savage@localhost/mono_flask'
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")  # new
	CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")

