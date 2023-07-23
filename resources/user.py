import logging

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
    verify_jwt_in_request,
)
from flask_restful import Resource
from models.api_key import ApiKey
from models.block_list import TokenBlocklist
from models.user import User


class CreateUser(Resource):
	"""
	This class represents a resource for creating a new user.
	"""
	def post(self):
		# get the username and email from the request body
		username = request.json.get("username")
		email = request.json.get("email")

		# check if a user with the same username or email already exists
		if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
			# return an error if a user with the same username or email already exists
			return make_response(jsonify({'msg': 'Select another username or email!'}), 400)

		# create a new user with the given username, email, and password
		new_user = User(username=username, email=email)
		new_user.set_password(request.json.get("password"))
		# add the new user to the database and commit the changes
		db.session.add(new_user)
		db.session.commit()
		response = 'User is created!'
		return make_response(response, 200)



class Login(Resource):
	"""
	This class represents a resource for logging in and handling JWT tokens.
	It includes two callback functions for checking the JWT status:
		- user_lookup_callback: looks up a user based on the JWT data
		- check_if_token_revoked: checks if a token has been revoked
	"""
	@jwt.user_lookup_loader
	def user_lookup_callback(self, jwt_data):
		"""
		Looks up a user based on the JWT data.
		:param jwt_data: the JWT data
		:return: the user with the specified ID, or None if no such user exists
		"""
		identity = jwt_data["sub"]
		return User.query.filter_by(id=identity).one_or_none()

	@jwt.token_in_blocklist_loader
	def check_if_token_revoked(self, jwt_payload: dict) -> bool:
		"""
		Checks if a token has been revoked.
		:param jwt_payload: the JWT payload
		:return: True if the token has been revoked, False otherwise
		"""
		jti = jwt_payload["jti"]
		token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
		return token is not None

	def post(self):
		"""
		Logs in a user and generates an access token.
		:return: the access token and the user's ID, or an error message if the login is unsuccessful
		"""
		# get the username and password from the request body
		username = request.json.get("username", None)
		password = request.json.get("password", None)
		# get the user with the given username
		user_login = User.query.filter_by(username=username).first()

		# check if the user exists and the password is correct
		if user_login is None or not user_login.check_password(password):
			# return an error if the login is unsuccessful
			return make_response(jsonify({"msg": 'Bad username or password'}), 401)

		# generate an access token for the user
		access_token = create_access_token(identity=user_login.id)
		# return the access token and the user's ID in the response
		response = jsonify({"token": access_token, "user_id": user_login.id})

		# add CORS headers to the response
		response.headers.add('Access-Control-Allow-Methods', "POST, GET, OPTIONS")
		response.headers.add('Access-Control-Allow-Headers',
							 "Origin, X-Api-Key, X-Requested-With, Content-Type, Accept, Authorization")
		response.headers.add('Access-Control-Allow-Origin', '*')
		response.headers.add('Content-Type', 'application/json')
		return make_response(response, 200)


class Logout(Resource):
	"""
	This class represents a resource for logging out and revoking JWT tokens.
	It includes a method for revoking an access token or refresh token.
	"""
	def delete(self):
		"""
		Revokes an access token or refresh token.
		:return: a message indicating that the token has been revoked, or an error if the token is invalid
		"""
		# verify the JWT in the request
		jwt_verif = verify_jwt_in_request()
		# get the JWT from the request
		token = get_jwt()
		# get the JWT ID and type
		jti = token["jti"]
		ttype = token["type"]
		# add the token to the blocklist
		db.session.add(TokenBlocklist(jti=jti, type=ttype))
		# commit the changes to the database
		db.session.commit()
		# return a message indicating that the token has been revoked
		return make_response(jsonify({"msg": f"{ttype.capitalize()} token successfully revoked!"}), 200)


class ChangePassword(Resource):
	"""
	This class represents a resource for changing a user's password.
	It includes a method for changing the password and revoking the user's JWT tokens.
	"""
	@jwt_required()
	def post(self):
		"""
		Changes a user's password and revokes their JWT tokens.
		:return: a message indicating that the password has been changed and the tokens have been revoked, or an error if the password is invalid
		"""
		# get the current user's ID from the JWT
		current_user = get_jwt_identity()
		# get the user with the given ID
		user_login = User.query.filter_by(id=current_user).first()
		# get the new password from the request body
		new_password = request.json.get("newPassword", None)
		# check if the new password is valid
		if user_login.check_password(new_password) is False:
			# set the user's password hash to the hashed version of the new password
			user_login.password_hash = user_login.set_password(new_password)
			# get the JWT from the request
			token = get_jwt()
			# get the JWT ID and type
			jti = token["jti"]
			ttype = token["type"]
			# add the token to the blocklist
			db.session.add(TokenBlocklist(jti=jti, type=ttype))
			# commit the changes to the database
			db.session.commit()
			# return a message indicating that the password has been changed and the tokens have been revoked
			return make_response(jsonify({"msg": "New password is successfully set!"}), 200)
		# return an error if the password is invalid
		else:
			return make_response(jsonify({"msg": "Password is not pass validation"}), 400)


"""""""""
class User(Resource):

	@jwt_required()
	def get(self):
		current_user = get_jwt_identity()
		user_login = user.User.query.get(current_user)

		if user_login is None:
			return make_response(jsonify({"msg": 'Current user is not valid!'}, 401))
		records = user.User.query.all()

		data = [{
				'id': user_login.id,
				'username': user_login.username,
				'api_key': user_login.api_key,
				'email': user_login.email
		} for user_login in records]
		return make_response(jsonify(data), 200)
"""""""""

class Apikey(Resource):
	"""
	This class represents a resource for inserting an API key.
	It includes a method for inserting an API key for a user.
	"""
	@jwt_required()
	def post(self):
		"""
		Inserts an API key for a user.
		:return: a message indicating success or an error if something went wrong
		"""
		# get the current user's ID from the JWT
		current_user = get_jwt_identity()
		# get the user with the given ID
		user_row = User.query.get(current_user)
		# get the user's ID
		user_id = user_row.id
		# get the API key and project name from the request body
		api_key_request = request.json.get('api_key', None)
		project = request.json.get('project', None)

		if user_row:
			# create a new API key object with the user's ID, project name, and API key
			key_row = ApiKey(
				user_id=user_id,
				project=project,
				key=api_key_request
			)
			# add the API key to the database
			db.session.add(key_row)
			# commit the changes to the database
			db.session.commit()
			# return a message indicating success
			return make_response(jsonify({'msg': 'Success, api key added!'}), 200)
		# return an error if something went wrong
		else:
			return make_response(jsonify({'msg': 'Something went wrong'}), 400)
