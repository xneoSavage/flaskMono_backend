from externals import db
from datetime import datetime
from models.account import Account


class Transaction(db.Model):
	__tablename__ = 'transactions'

	id = db.Column(db.Integer, primary_key=True)
	loaded_at = db.Column(db.DateTime(timezone='UTC'), default=datetime.utcnow())
	account_id = db.Column(db.Integer, db.ForeignKey(Account.id, onupdate='cascade', ondelete='cascade'))
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
	account = db.relationship('Account', backref=db.backref('account', uselist=False))
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
