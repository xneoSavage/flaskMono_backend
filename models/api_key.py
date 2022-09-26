import enum

from externals import db
from datetime import datetime
from models.user import User

class MyEnum(enum.Enum):
	status_new = 'new'
	status_active = 'active'
	status_deactivated = 'deactivated'
	status_deleted = 'deleted'


class ApiKey(db.Model):
	__tablename__ = 'api_keys'

	id = db.Column(db.Integer, primary_key='true')
	created_at = db.Column(db.DateTime, default=datetime.utcnow())
	updated_at = db.Column(db.DateTime, default=datetime.utcnow())
	key = db.Column(db.String, nullable=False, unique=True)
	status = db.Column(db.String, db.Enum(MyEnum), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey(User.id, ondelete='cascade', onupdate='cascade'))
	project = db.Column(db.String, nullable=False, default='mono')
# constraint
