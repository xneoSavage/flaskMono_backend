import os


basedir = os.path.abspath(__file__)

class Config(object):
	SECRET_KEY = 'SECRET_KEY'
	# db connection
	#SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:2332@localhost/monoFlask'
	#SQLALCHEMY_DATABASE_URI = os.getenv('DB_URI') #AZURE
	SQLALCHEMY_DATABASE_URI = os.getenv('DB_URI_ELEPHANT') #ELEPHANT_SQL
	SQLALCHEMY_TRACK_MODIFICATIONS = False
