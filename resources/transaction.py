import time

from externals import db, jwt
from flask_jwt_extended import jwt_required, get_jwt, create_access_token, get_jwt_identity
from flask_restful import Resource
from flask import jsonify, make_response, request
from models.user import User
from models.api_key import ApiKey
from models.account import Account
from models.transaction import Transaction
from models.block_list import TokenBlocklist
import monobank
from datetime import datetime, timedelta, date
import pandas as pd

date.today()

class LoadTransaction(Resource):
    @jwt_required()
    def post(self):
        # get all user accounts
        account_table = Account.query.filter_by(user_id=get_jwt_identity()).all()
        existed_accounts = []
        [existed_accounts.append(account_id.account_id) for account_id in account_table]

        # get mono token
        token_mono = ApiKey.query.filter_by(user_id=get_jwt_identity()).first()
        token_mono = token_mono.key
        mono = monobank.Client(token_mono)

        range_date = pd.date_range(start=date(2017, 11, 1), end=date.today())
        range_date = range_date[::-1]
        range_date = range_date[::30]

        for account in existed_accounts:
            account_id = Account.query.filter_by(account_id=account).first()
            last_transaction = Transaction.query.filter_by(account_id=account_id.id).first()
            count = 0
            for end_date in range_date:
                transactions_id = Transaction.query.filter_by(account_id=account_id.id).all()
                existed_transactions = []
                [existed_transactions.append(transaction_id.transaction_id)
                    for transaction_id in transactions_id]
                start_date = end_date - timedelta(days=29)
                time.sleep(60)

                try:
                    loaded_transactions = mono.get_statements(account, start_date, end_date)
                    for transaction in loaded_transactions:
                        if transaction['id'] not in existed_transactions and transaction['time']:
                            if transaction['amount'] > 0:
                                transaction_type = 'credit'
                            else:
                                transaction_type = 'debit'

                            transactions_table = Transaction(transaction_id=transaction['id'],
                                                             transaction_type=transaction_type,
                                                             created_at=datetime.fromtimestamp(transaction['time']),
                                                             loaded_at=datetime.utcnow(),
                                                             account_id=account_id.id,
                                                             description=transaction['description'],
                                                             mcc=transaction['mcc'],
                                                             original_mcc=transaction['originalMcc'],
                                                             amount=transaction['amount'],
                                                             operation_amount=transaction['operationAmount'],
                                                             currency_code=transaction['currencyCode'],
                                                             commission_rate=transaction['commissionRate'],
                                                             cashback_amount=transaction['cashbackAmount'],
                                                             balance=transaction['balance'],
                                                             hold=transaction['hold'])
                            db.session.add(transactions_table)
                            db.session.commit()
                        else:
                            pass
                except monobank.errors.Error:
                    pass

        return make_response(jsonify({"msg": 'Everything is ok'}), 200)

    @jwt_required()
    def put(self):

        account_table = Account.query.filter_by(user_id=get_jwt_identity()).order_by(Account.id.asc()).all()
        existed_accounts = []
        [existed_accounts.append(account_id.account_id) for account_id in account_table]

        token_mono = ApiKey.query.filter_by(user_id=get_jwt_identity()).first()
        token_mono = token_mono.key
        mono = monobank.Client(token_mono)
        for account in existed_accounts:
            account_id = Account.query.filter_by(account_id=account).first()
            count = 2
            print(f"Count is {count}")
            transactions_id = Transaction.query.filter_by(account_id=account_id.id).order_by(Transaction.created_at.desc()).first()
            if transactions_id:
                range_date = pd.date_range(start=transactions_id.created_at, end=date.today())
                time.sleep(60)
                try:
                    if len(range_date) <= 30 and count > 0:
                        loaded_transactions = mono.get_statements(account, transactions_id.created_at, datetime.utcnow())
                    elif len(range_date) > 30 and count > 0:
                        return make_response(jsonify({"msg": 'Difference between last transaction date and date now\n'
                                                             'is bigger than 30 days, load transactions!'}))

                    for transaction in loaded_transactions:
                        if transactions_id and transaction['time'] > datetime.timestamp(transactions_id.created_at):
                            if transaction['amount'] > 0:
                                transaction_type = 'credit'
                            else:
                                transaction_type = 'debit'

                            transactions_table = Transaction(transaction_id=transaction['id'],
                                                             transaction_type=transaction_type,
                                                             created_at=datetime.fromtimestamp(transaction['time']),
                                                             loaded_at=datetime.utcnow(),
                                                             account_id=account_id.id,
                                                             description=transaction['description'],
                                                             mcc=transaction['mcc'],
                                                             original_mcc=transaction['originalMcc'],
                                                             amount=transaction['amount'],
                                                             operation_amount=transaction['operationAmount'],
                                                             currency_code=transaction['currencyCode'],
                                                             commission_rate=transaction['commissionRate'],
                                                             cashback_amount=transaction['cashbackAmount'],
                                                             balance=transaction['balance'],
                                                             hold=transaction['hold'])
                            db.session.add(transactions_table)
                            db.session.commit()

                        else:
                            count -= 1
                except monobank.errors.Error:
                    pass

        return make_response(jsonify({'msg': 'Transactions loaded'}), 200)


class AllTransactions(Resource):
    @jwt_required()
    def get(self):
        description = request.json.get("description", None)
        transactions = Transaction.query.join(Account, Transaction.account).join(User, Account.user)\
            .filter_by(id=get_jwt_identity()).all()
        merchants = Transaction.query.distinct(Transaction.description).all()
        one_merch = Transaction.query.filter_by(description=description).all()
        merch = [{
            "merchant": m.description
        } for m in merchants]
        data = [{
            "id": transaction.transaction_id,
            "amount": transaction.amount,
            "time": transaction.created_at,
            "description": transaction.description

        } for transaction in transactions]
        merchant = [{
            'id': one_mech.id,
            'transaction_id': one_mech.transaction_id,
            'amount': one_mech.amount,
            'created_at': one_mech.created_at
        } for one_mech in one_merch]
        return make_response(jsonify({"msg": data}), 200)