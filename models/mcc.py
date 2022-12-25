from externals import db
from datetime import datetime


class MccCode(db.Model):
    __tablename__ = 'mcc_codes'

    id = db.Column(db.Numeric, primary_key=True)
    mcc_code = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(100), nullable=False)