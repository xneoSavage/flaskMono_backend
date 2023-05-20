import os


basedir = os.path.abspath(__file__)

class Config(object):
	SECRET_KEY = 'SECRET_KEY'
	# db connection
	SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:savage@localhost/mono_flask'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
