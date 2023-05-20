from externals import db
from datetime import datetime
from models.transaction import Transaction

class MccCode(db.Model):
    __tablename__ = 'mcc_codes'

    id = db.Column(db.Numeric, primary_key=True)
    mcc_code = db.Column(db.Integer)
    description = db.Column(db.String(100))
    short_description = db.Column(db.String(100))