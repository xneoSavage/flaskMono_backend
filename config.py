import os

import app

basedir = os.path.abspath(__file__)

class Config(object):
	SECRET_KEY = 'SECRET_KEY'
	MONOBANK_TOKEN = os.environ.get('MONO_TOKEN')
	# db connection
	SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:savage@localhost/test_flask'
	SQLALCHEMY_TRACK_MODIFICATIONS = False

