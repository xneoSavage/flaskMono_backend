import time

import monobank
import pandas as pd
from datetime import (
    date,
    datetime,
    timedelta,
)
from externals import (
    db,
    jwt,
    prev_month,
)
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
from models.mcc import MccCode
from models.transaction import Transaction
from models.user import User
from sqlalchemy import func, extract
from resources.account import LoadAccount


class LoadTransaction(Resource):
    """
       Class for updating transactions for a user's accounts in the database from the Monobank API.
       Requires a valid JWT for access.
    """

    @jwt_required()
    def post(self):
        """
            Update the Transactions table with information from the Monobank API for the user's accounts.
            :return: 200 if successful, 400 if something went wrong
        """
        # Update user and account information
        LoadAccount.post(self)
        # Get a list of the user's accounts
        account_table = Account.query.filter_by(user_id=get_jwt_identity()).all()
        existed_accounts = []
        [existed_accounts.append(account_id.account_id) for account_id in account_table]

        # Get the Mono token
        token_mono = ApiKey.query.filter_by(user_id=get_jwt_identity()).first()
        token_mono = token_mono.key
        mono = monobank.Client(token_mono)

        # Set up a range of dates to query the Monobank API for transactions
        range_date = pd.date_range(start=date(2017, 11, 1), end=date.today())
        range_date = range_date[::-1]
        range_date = range_date[::30]

        # Iterate through the user's accounts
        for account in existed_accounts:

            # Get the account ID from the Accounts table
            account_id = Account.query.filter_by(account_id=account).first()
            last_transaction = Transaction.query.filter_by(account_id=account_id.id).first()
            count = 0

            # Iterate through the date range
            for end_date in range_date:

                # Get a list of existing transactions for the account
                transactions_id = Transaction.query.filter_by(account_id=account_id.id).all()
                existed_transactions = []
                [existed_transactions.append(transaction_id.transaction_id)
                    for transaction_id in transactions_id]

                # Set the start date for the transaction query
                start_date = end_date - timedelta(days=29)
                time.sleep(60)

                try:
                    # Get transactions from the Monobank API
                    loaded_transactions = mono.get_statements(account, start_date, end_date)
                    # Iterate through the transactions
                    for transaction in loaded_transactions:
                        # Insert the transaction into the Transactions table if it doesn't already exist
                        if transaction['id'] not in existed_transactions and transaction['time']:
                            # Determine if the transaction is a credit or debit
                            if transaction['amount'] > 0:
                                transaction_type = 'credit'
                            else:
                                transaction_type = 'debit'
                            # Create a new Transaction object and insert it into the table
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
        """
            Update the Transactions table with new transactions from the Monobank API for a user's accounts.
            :return: 200 if successful, 400 if something went wrong
        """
        # Get a list of the user's accounts
        account_table = Account.query.filter_by(user_id=get_jwt_identity()).order_by(Account.id.asc()).all()
        existed_accounts = []
        [existed_accounts.append(account_id.account_id) for account_id in account_table]
        # Get the Mono token
        token_mono = ApiKey.query.filter_by(user_id=get_jwt_identity()).first()
        token_mono = token_mono.key
        mono = monobank.Client(token_mono)
        # Iterate through the user's accounts
        for account in existed_accounts:
            # Get the account ID from the Accounts table
            account_id = Account.query.filter_by(account_id=account).first()
            count = 2
            print(f"Count is {count}")
            # Get the date of the last transaction for the account
            transactions_id = Transaction.query.filter_by(account_id=account_id.id).order_by(Transaction.created_at.desc()).first()
            # Set up a range of dates to query the Monobank API for transactions
            if transactions_id:
                range_date = pd.date_range(start=transactions_id.created_at, end=date.today())
                time.sleep(60)
                try:
                    # If the difference between the last transaction date and today is less than 30 days, load the transactions
                    if len(range_date) <= 30 and count > 0:
                        loaded_transactions = mono.get_statements(account, transactions_id.created_at, (datetime.utcnow()))
                        # If the difference is greater than 30 days, return an error message
                    elif len(range_date) > 30 and count > 0:
                        return make_response(jsonify({"msg": 'Difference between last transaction date and date now\n'
                                                             'is bigger than 30 days, load transactions! Try to use POST instead!'}))
                    # Iterate through the transactions
                    for transaction in loaded_transactions:
                        # Insert the transaction into the Transactions table if it is newer than the last transaction
                        if transactions_id and transaction['time'] > datetime.timestamp(transactions_id.created_at):
                            # Determine if the transaction is a credit or debit
                            if transaction['amount'] > 0:
                                transaction_type = 'credit'
                            else:
                                transaction_type = 'debit'
                            # Create a new Transaction object and insert it into the table
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


        # AllTransactions is a Flask RESTful resource for handling HTTP GET requests for retrieving all transactions
# for the currently authenticated user. It is implemented using the Flask-JWT-Extended library for JWT
# (JSON Web Token) authentication.
class AllTransactions(Resource):
    # Handles a GET request to retrieve all transactions for the currently authenticated user. This route is
    # protected with the Flask-JWT-Extended library's jwt_required decorator, which ensures that the request
    # has a valid JWT in the authorization header.
    @jwt_required()
    def get(self):
        """
        Handles a GET request to retrieve all transactions for the currently authenticated user. This route is
        protected with the Flask-JWT-Extended library's jwt_required decorator, which ensures that the request
        has a valid JWT in the authorization header.
        """
        # Get the user's ID from the JWT stored in the authorization header of the request.
        user_id = get_jwt_identity()

        # Query the database for all transactions made by the authenticated user and join the Account and User
        # tables to get the associated account and user information. The transactions are ordered by their
        # creation time in descending order.
        transactions = Transaction.query.join(Account, Transaction.account).join(User, Account.user) \
            .filter_by(id=user_id).order_by(Transaction.created_at.desc()).all()

        # Construct a list of dictionaries containing the transaction information to be returned in the response.
        data = [{
            "id": transaction.transaction_id,
            "amount": transaction.amount,
            "type": transaction.transaction_type,
            "currency_code": transaction.currency_code,
            "cashback_amount": transaction.cashback_amount,
            "balance": transaction.balance,
            "mcc": transaction.mcc,
            "time": transaction.created_at,

            "description": transaction.description
        } for transaction in transactions]

        # Return a Flask response object containing the list of transactions as a JSON object, along with a status
        # code of 200 to indicate a successful request.
        return make_response(jsonify(data), 200)


class CreditTransactions(Resource):
    """
    Resource for getting a list of credit transactions for the authenticated user in the previous month.
    """
    # require JWT token for this route
    @jwt_required()
    def get(self):
        """
        GET request to get a list of credit transactions for the authenticated user in the previous month.
        Returns:
            200: a list of dictionaries representing each transaction
        """
        # get the start and end dates for the previous month
        prev_month_start, prev_month_end = prev_month()

        # get all transactions for the authenticated user in the previous month
        query = db.session.query(
            Transaction.transaction_id,
            Transaction.amount,
            Transaction.created_at,
            Transaction.description,
            Transaction.transaction_type,
            Transaction.mcc,
            MccCode.description.label('mcc_description')
        )\
            .join(Account, Transaction.account_id == Account.id) \
            .join(MccCode, Transaction.mcc == MccCode.mcc_code) \
            .join(User, Account.user_id == User.id) \
            .filter_by(id=get_jwt_identity()) \
            .where(Transaction.created_at.between(prev_month_start, prev_month_end), Transaction.transaction_type=='credit') \
            .order_by(Transaction.amount.asc()).all()


        # build a list of dictionaries representing each transaction
        data = [{
            "id": transaction.transaction_id,
            "amount": transaction.amount,
            "time": transaction.created_at,
            "description": transaction.description,
            "type": transaction.transaction_type,
            "mcc": transaction.mcc,
            "mcc_description": transaction.mcc_description
        } for transaction in query]

        # return the list of transactions in the response
        return make_response(jsonify(data), 200)


class TransStatisticDebitCredit(Resource):
    """
      This class handles getting statistics for transactions in the previous month, grouped by account
      and transaction type.
    """
    @jwt_required()
    def get(self):
        """
              This method gets the statistics for transactions in the previous month, grouped by account
              and transaction type.
              :return: A response containing the list of statistics for each account and transaction type,
              along with the start and end dates of the previous month.
        """

        prev_month_start, prev_month_end = prev_month()

        # get statistics for transactions in the previous month, grouped by account and transaction type
        query = db.session.query(
            # use a case statement to sum up the amounts for debit and credit transactions separately
            db.case((Transaction.transaction_type == 'debit', func.sum(Transaction.amount)),
                     (Transaction.transaction_type == 'credit', func.sum(Transaction.amount))).label('sum'),
            func.count(Transaction.id).label('count'),
            func.max(Transaction.amount).label('max_amount'),
            Account.account_id, Account.type,
            Account.credit_limit, Transaction.transaction_type,
            Account.currency_code, Transaction.description
        ) \
            .join(Account, Account.id == Transaction.account_id) \
            .join(User, User.id == Account.user_id) \
            .filter_by(id=get_jwt_identity()) \
            .where(Transaction.created_at.between(prev_month_start, prev_month_end)) \
            .group_by(Account.account_id, Account.type, Account.credit_limit, Account.currency_code,
                      Transaction.transaction_type, Transaction.description).all()

        # build a list of dictionaries representing the statistics for each account and transaction type
        data = [{
            "account_id": result.account_id,
            "sum": result.sum,
            "card_type": result.type,
            "credit_limit": result.credit_limit,
            "transactions_type": result.transaction_type,
            "count": result.count,
            "max_amount": result.max_amount,
            "currency_code": result.currency_code,
            "description": result.description,
        } for result in query]

        # add the start and end dates of the previous month to the response
        data[0]['prev_month_start'] = prev_month_start
        data[0]['prev_month_end'] = prev_month_end
        return make_response(jsonify(data), 200)


class AmountByMCC(Resource):
    """
      Resource for retrieving the sum of transaction amounts by MCC code and transaction type for a given user.
    """

    @jwt_required()
    def get(self):
        """
             Retrieve the sum of transaction amounts by MCC code and transaction type for the authenticated user, grouped by month and year.
             :return: a list of dictionaries representing the sum of amounts for each MCC code and transaction type.
        """
        # get the sum of transaction amounts by MCC code and transaction type for the authenticated user,
        # grouped by month and ordered by transaction type
        request.headers.get('Authorization')

        query = db.session.query(
            func.sum(Transaction.amount).label('amount'),
            MccCode.mcc_code,
            MccCode.short_description,
            Transaction.transaction_type,
            func.date_trunc('month', Transaction.created_at).label('month'),
            extract('year', Transaction.created_at).label('year')
        ) \
            .join(Account, Transaction.account_id == Account.id) \
            .join(MccCode, MccCode.mcc_code == Transaction.mcc) \
            .join(User, User.id == Account.user_id) \
            .filter(User.id == get_jwt_identity()) \
            .group_by(MccCode.mcc_code, MccCode.short_description, Transaction.transaction_type, 'month', 'year') \
            .order_by(Transaction.transaction_type.desc(), 'year', 'month')

        # build a list of dictionaries representing the sum of amounts for each MCC code, transaction type, and month
        data = [{
            "month": result.month,
            "year": result.year,
            "amount": result.amount,
            "mcc_code": result.mcc_code,
            "mcc_description": result.short_description,
            "transaction_type": result.transaction_type
        } for result in query]

        # return the list of MCC codes, transaction types, and months in the response
        return make_response(jsonify(data), 200)




class MccAmountMonth(Resource):
    """
    A class representing the endpoint for retrieving transactions filtered by MCC code.
    """

    @jwt_required()
    def post(self):
        """
        This method handles GET requests to the endpoint. It retrieves a list of transactions for the authenticated user
        in the previous month that match the MCC code provided in the request body. The transactions are ordered by
        amount in descending order.

        :return: A list of transactions in the response, with a status code of 200.
        """
        # get the start and end dates for the previous month
        prev_month_start, prev_month_end = prev_month()
        # get the MCC code from the request body
        request_mcc = request.json.get("mcc_code", None)
        request_transaction_type = request.json.get("transaction_type", None)

        # get the transactions for the given MCC code and the authenticated user in the previous month,
        # ordered by amount in descending order
        query = (
            db.session.query(
                func.date_trunc("month", Transaction.created_at).label("date"),
                func.sum(Transaction.amount).label("amount"),
                Transaction.transaction_type,
                Transaction.mcc,
                MccCode.short_description.label("mcc_description"),
            )
            .join(Account, Transaction.account_id == Account.id)
            .join(MccCode, MccCode.mcc_code == Transaction.mcc)
            .join(User, User.id == Account.user_id)
            .filter(User.id == get_jwt_identity())
            .filter(Transaction.mcc == request_mcc)
            .filter(Transaction.transaction_type == request_transaction_type)
            .group_by(
                Transaction.transaction_type,
                "date",
                "mcc_description",
                Transaction.mcc,
            )
            .order_by(func.date_trunc("month", Transaction.created_at).desc())
        )

        # build a list of dictionaries representing each transaction
        # build a list of dictionaries representing each transaction
        data = [{
            "date": result.date,
            "amount": result.amount,
           # "transaction_description": result.description,
            "transaction_type": result.transaction_type,
            "mcc_code": result.mcc,
            "mcc_description": result.mcc_description
        } for result in query]
        # return the list of transactions in the response
        return make_response(jsonify(data), 200)


class TransByMCC(Resource):
        """
        A class representing the endpoint for retrieving transactions filtered by MCC code.
        """

        @jwt_required()
        def post(self):
            """
            This method handles GET requests to the endpoint. It retrieves a list of transactions for the authenticated user
            in the previous month that match the MCC code provided in the request body. The transactions are ordered by
            amount in descending order.

            :return: A list of transactions in the response, with a status code of 200.
            """
            # get the start and end dates for the previous month
            prev_month_start, prev_month_end = prev_month()
            # get the MCC code from the request body
            request_mcc = request.json.get("mcc_code", None)
            request_month = request.json.get("month", None)
            request_transaction_type = request.json.get("transaction_type", None)

            # get the transactions for the given MCC code and the authenticated user in the previous month,
            # ordered by amount in descending order
            query = (db.session.query(Transaction.created_at,
                                      Transaction.amount,
                                      Transaction.description,
                                      Transaction.transaction_type,
                                      Transaction.mcc,
                                      MccCode.short_description.label('mcc_description'))
                     .join(Account, Transaction.account_id == Account.id)
                     .join(MccCode, MccCode.mcc_code == Transaction.mcc)
                     .join(User, User.id == Account.user_id)
                     .filter(User.id == get_jwt_identity())
                     .filter(func.date_trunc('month', Transaction.created_at).label('month') == request_month)
                     .filter(Transaction.mcc == request_mcc)
                     .filter(Transaction.transaction_type == request_transaction_type)
                     .group_by(Transaction.transaction_type,
                               Transaction.created_at,
                               Transaction.amount,
                               Transaction.description,
                               Transaction.mcc,
                               MccCode.short_description)
                     .order_by(Transaction.amount.desc()))

            # build a list of dictionaries representing each transaction
            # build a list of dictionaries representing each transaction
            data = [{
                "created_at": result.created_at,
                "amount": result.amount,
                "transaction_description": result.description,
                "transaction_type": result.transaction_type,
                "mcc_code": result.mcc,
                "mcc_description": result.mcc_description
            } for result in query]
            # return the list of transactions in the response
            return make_response(jsonify(data), 200)