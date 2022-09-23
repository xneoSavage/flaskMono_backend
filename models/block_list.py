from flask_jwt_extended import get_current_user
from externals import db
from datetime import datetime
from models.user import User


class TokenBlocklist(db.Model):
	__tablename__ = 'token_block_list'

	id = db.Column(db.Integer, primary_key=True)
	jti = db.Column(db.String(36), nullable=False, index=True)
	type = db.Column(db.String(16), nullable=False)
	user_id = db.Column(
		db.ForeignKey(User.id),
		default=lambda: get_current_user().id,
		nullable=False,
	)
	created_at = db.Column(
		db.DateTime,
		default=datetime.utcnow(),
		nullable=False,
	)
