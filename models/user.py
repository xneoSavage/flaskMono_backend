from externals import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import UserMixin
# from app import login
from hashlib import md5


class User(db.Model):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	created_at = db.Column(db.DateTime, default=datetime.utcnow())
	updated_at = db.Column(db.DateTime)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	client_id = db.Column(db.String(30), unique=True)
	webhook_url = db.Column(db.String(39))
	name = db.Column(db.String(100))
	permissions = db.Column(db.String(30))
	api_key = db.Column(db.String(44), unique=True)

	def __repr__(self):
		return f'User {self.username}'

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)
		return self.password_hash

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)
