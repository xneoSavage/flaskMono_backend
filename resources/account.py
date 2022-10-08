from externals import db, jwt
from flask_jwt_extended import jwt_required, get_jwt, create_access_token, get_jwt_identity
from flask_restful import Resource
from flask import jsonify, make_response, request
from models.user import User
from models.api_key import ApiKey
from models.account import Account
from models.block_list import TokenBlocklist
import monobank
from datetime import datetime


class LoadAccount(Resource):
    """
    update Users table (name, client_id, permissions)
    insert Account data to table Accounts
    :return:
    200 if everything is ok, row inserting
    400 if smth went wrong
    """
    @jwt_required()
    def post(self):

        # make list of existed accounts, for prevent unique constraint
        account_table = Account.query.filter_by(user_id=get_jwt_identity()).all()
        existed_accounts = []
        [existed_accounts.append(account_id.account_id) for account_id in account_table]

        # get mono token
        token_mono = ApiKey.query.filter_by(user_id=get_jwt_identity()).first()
        token_mono = token_mono.key
        mono = monobank.Client(token_mono)
        client_data = mono.get_client_info()

        # update table Users with data from mono
        row_user = User.query.filter_by(id=get_jwt_identity()).first()
        row_user.name = client_data['name']
        row_user.client_id = client_data['clientId']
        row_user.permissions = client_data['permissions']
        row_user.updated_at = datetime.utcnow()
        token_mono.status = 'active'
        db.session.add(row_user)

        for account in client_data['accounts']:

            # update account if exist
            if account['id'] in existed_accounts:
                row_exist_account = Account.query.filter_by(account_id=account['id']).first()
                row_exist_account.balance = account['balance']
                row_exist_account.credit_limit = account['creditLimit']
                row_exist_account.updated_at = datetime.utcnow()
                db.session.add(row_exist_account)

            # insert accounts from mono
            else:
                row_account = Account(
                    user_id=get_jwt_identity(),
                    account_id=account['id'],
                    send_id=account['sendId'],
                    currency_code=account['currencyCode'],
                    cashback_type=account['cashbackType'],
                    balance=account['balance'],
                    credit_limit=account['creditLimit'],
                    masked_pan=account['maskedPan'][0],
                    type=account['type'],
                    iban=account['iban']
                )
                token_mono.status = 'active'
                db.session.add(token_mono)
                db.session.add(row_account)

        db.session.commit()
        return make_response(jsonify({"msg": client_data}), 200)
