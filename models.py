from flask_jwt_extended import get_current_user

from app import db
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import UserMixin
# from app import login
from hashlib import md5


class Customer(db.Model):
	__tablename__ = 'customers'

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

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)


class Account(db.Model):
	__tablename__ = 'accounts'

	id = db.Column(db.Integer, primary_key=True)
	loaded_at = db.Column(db.DateTime, default=datetime.utcnow())
	customer_id = db.Column(db.ForeignKey('customers.id', ondelete='cascade', onupdate='cascade'))
	card_id = db.Column(db.String(30), unique=True)
	send_id = db.Column(db.String(30), unique=True)
	currency_code = db.Column(db.Integer)
	cashback_type = db.Column(db.String(30))
	balance = db.Column(db.Integer)
	credit_limit = db.Column(db.Integer)
	masked_pan = db.Column(db.String(30), nullable=False)
	type = db.Column(db.String(30))
	iban = db.Column(db.String(30))

	def __repr__(self):
		return f'Card type {self.type}'


class Transaction(db.Model):
	__tablename__ = 'transactions'

	id = db.Column(db.Integer, primary_key=True)
	loaded_at = db.Column(db.DateTime, default=datetime.utcnow())
	account_id = db.Column(db.Integer, db.ForeignKey('accounts.id', onupdate='cascade', ondelete='cascade'))
	created_at = db.Column(db.DateTime)
	transaction_id = db.Column(db.String(30), unique=True)
	# card_id = Column(String(30), ForeignKey('accounts.card_id'))#,ForeignKey(accounts.card_id)
	description = db.Column(db.String(255))
	transaction_type = db.Column(db.String(10))
	mcc = db.Column(db.Integer)
	original_mcc = db.Column(db.Integer)
	amount = db.Column(db.Integer)
	operation_amount = db.Column(db.Integer)
	currency_code = db.Column(db.Integer)
	commission_rate = db.Column(db.Integer)  # можливо доведеться змінити тип, подивитися по даних
	cashback_amount = db.Column(db.Integer)
	balance = db.Column(db.Integer)
	hold = db.Column(db.Boolean)
	comment = db.Column(db.String(200))
	receipt_id = db.Column(db.String(25))
	invoice_id = db.Column(db.String(30))
	counter_edrpou = db.Column(db.String(30))
	counter_iban = db.Column(db.String(50))

	@property
	def serialize(self):
		"""Return object data in easily serializable format"""
		return {
			'id': self.id,
			'updated_at': self.updated_at,
			# This is an example how to deal with Many2Many relations
		}

	'''''''''
	def __repr__(self):
		return 
	'''''''''


class TokenBlocklist(db.Model):
	__tablename__ = 'token_block_list'

	id = db.Column(db.Integer, primary_key=True)
	jti = db.Column(db.String(36), nullable=False, index=True)
	type = db.Column(db.String(16), nullable=False)
	user_id = db.Column(
		db.ForeignKey(Customer.id),
		default=lambda: get_current_user().id,
		nullable=False,
	)
	created_at = db.Column(
		db.DateTime,
		default=datetime.utcnow(),
		nullable=False,
	)
