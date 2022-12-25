import time
from datetime import datetime

from externals import db, jwt
from flask import (
    jsonify,
    make_response,
    request,
)
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_restful import Resource
from models.account import Account
from models.api_key import ApiKey
from models.block_list import TokenBlocklist
from models.user import User
import monobank


class LoadAccount(Resource):
    """
      Class for updating user and account information in the database from the Monobank API.
      Requires a valid JWT for access.
      """
    @jwt_required()
    def post(self):
        """
          Update the Users table with name, client_id, and permissions data from the Monobank API.
          Insert Account data into the Accounts table.
          :return: 200 if successful, 400 if something went wrong
        """
        # Check if the API key is active

        api_key_status = ApiKey.query.filter_by(user_id=get_jwt_identity()).first()
        existed_accounts = []
        if api_key_status.status == 'active':
        # Create a list of existing accounts to prevent unique constraint violations

            account_table = Account.query.filter_by(user_id=get_jwt_identity())
            if account_table is not None:
                [existed_accounts.append(account_id.account_id) for account_id in account_table]

        # Get client data from the Monobank API

        token_mono_table = ApiKey.query.filter_by(user_id=get_jwt_identity()).first()
        token_mono = token_mono_table.key
        mono = monobank.Client(token_mono)
        try:
            client_data = mono.get_client_info()

            # Update or insert accounts into the Accounts table
            row_user = User.query.filter_by(id=get_jwt_identity()).first()
            row_user.name = client_data['name']
            row_user.client_id = client_data['clientId']
            row_user.permissions = client_data['permissions']
            row_user.updated_at = datetime.utcnow()
            token_mono_table.status = 'active'
            db.session.add(row_user)

            for account in client_data['accounts']:

                    # Update existing account
                    if account['id'] in existed_accounts:
                        row_exist_account = Account.query.filter_by(account_id=account['id']).first()
                        row_exist_account.balance = account['balance']
                        row_exist_account.credit_limit = account['creditLimit']
                        row_exist_account.updated_at = datetime.utcnow()
                        db.session.add(row_exist_account)

                    # Insert new account
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

                        db.session.add(row_account)

                    db.session.commit()
        except monobank.errors.TooManyRequests: time.sleep(60)
        return make_response(jsonify({"msg": client_data}), 200)


class AccountsData(Resource):
    """
       This class represents a resource for retrieving data about accounts.

       The resource requires a JSON Web Token (JWT) to be included in the request header
       in order to authenticate the user making the request.

       The data retrieved includes the name of the user associated with the account, the balance,
       currency code, credit limit, type, IBAN, and masked PAN of the account. The accounts are
       returned in a list, sorted in descending order by balance.
       """
    @jwt_required()
    def get(self):
        """
        Handle a GET request to retrieve data about accounts.

        Returns:
            A response object containing the data about the accounts in JSON format, with a
            status code of 200.
        """
        # description = request.json.get("description", None)
        accounts = Account.query.filter_by(user_id=get_jwt_identity()).order_by(Account.balance.desc()).all()
        accounts_data = Account.query.join(User, Account.user_id==User.id)\
            .filter_by(id=get_jwt_identity())\
            .order_by(Account.balance.desc())\
            .all()
        data = [{
            "user_name": account.user.name,
            "balance": account.balance,
            "currency": account.currency_code,
            "credit_limit": account.credit_limit,
            "type": account.type,
            "iban": account.iban,
            "masked_pan": account.masked_pan
        } for account in accounts_data]

        return make_response(jsonify(data), 200)