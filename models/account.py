from externals import db
from datetime import datetime
from models.user import User


class Account(db.Model):

	__tablename__ = 'accounts'

	id = db.Column(db.Integer, primary_key=True)
	loaded_at = db.Column(db.DateTime, default=datetime.utcnow())
	updated_at = db.Column(db.DateTime(timezone='UTC'), default=datetime.utcnow())
	user_id = db.Column(db.ForeignKey(User.id, ondelete='cascade', onupdate='cascade'))
	account_id = db.Column(db.String(30), unique=True)
	send_id = db.Column(db.String(30), unique=True)
	currency_code = db.Column(db.Integer)
	cashback_type = db.Column(db.String(30))
	balance = db.Column(db.Integer)
	credit_limit = db.Column(db.Integer)
	masked_pan = db.Column(db.String(16), nullable=False)
	type = db.Column(db.String(30))
	iban = db.Column(db.String(34))

	def __repr__(self):
		return f'Card type {self.type}'
