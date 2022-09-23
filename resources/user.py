from externals import db, jwt
from flask_jwt_extended import jwt_required, get_jwt, create_access_token, get_jwt_identity
from flask_restful import Resource
from flask import jsonify, make_response, request
import models.user
from models.block_list import TokenBlocklist


class CreateUser(Resource):

	def post(self):
		username = request.json.get("username")
		email = request.json.get("email")

		if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
			return make_response(jsonify({'msg': 'Select another username or email!'}), 400)

		user = User(username=username, email=email)
		user.set_password(request.json.get("password"))
		db.session.add(user)
		db.session.commit()
		response = jsonify({"msg": "User created successfully!"})
		response.headers.add('Access-Control-Allow-Origin', '*')
		response.headers.add('Content-Type', 'Authorization')
		return make_response(response, 200)


class Login(Resource):
	"""
	2 callback functions for check jwt status
	"""
	@jwt.user_lookup_loader
	def user_lookup_callback(self, jwt_data):
		identity = jwt_data["sub"]
		return User.query.filter_by(id=identity).one_or_none()


	@jwt.token_in_blocklist_loader
	def check_if_token_revoked(self, jwt_payload: dict) -> bool:
		jti = jwt_payload["jti"]
		token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
		return token is not None

	def post(self):

		username = request.json.get("username", None)
		password = request.json.get("password", None)
		user = models.user.User.query.filter_by(username=username).first()

		if user is None or not user.check_password(password):
			return make_response(jsonify({"msg": 'Bad username or password'}), 401)

		access_token = create_access_token(identity=user.id)
		response = jsonify({"token": access_token, "user_id": user.id})

		response.headers.add('Access-Control-Allow-Methods', "POST, GET, OPTIONS")
		response.headers.add('Access-Control-Allow-Headers', "Origin, X-Api-Key, X-Requested-With, Content-Type, Accept, Authorization")
		response.headers.add('Access-Control-Allow-Origin', 'http://192.168.1.47')
		response.headers.add('Content-Type', 'application/json')
		return make_response(response, 200)


class Logout(Resource):

	@jwt_required()
	def delete(self):
		token = get_jwt()
		jti = token["jti"]
		ttype = token["type"]
		db.session.add(TokenBlocklist(jti=jti, type=ttype))
		db.session.commit()
		return make_response(jsonify({"msg": f"{ttype.capitalize()} token successfully revoked!"}), 200)


class ChangePassword(Resource):
	@jwt_required()
	def post(self):
		current_user = get_jwt_identity()
		user = User.query.filter_by(id=current_user).first()
		new_password = request.json.get("newPassword", None)
		if user.check_password(new_password) is False:
			user.password_hash = user.set_password(new_password)
			token = get_jwt()
			jti = token["jti"]
			ttype = token["type"]
			db.session.add(TokenBlocklist(jti=jti, type=ttype))
			db.session.commit()
			return make_response(jsonify({"msg": "New password is successfully set!"}), 200)

		else:
			return make_response(jsonify({"msg": "Password is not pass validation"}), 400)


class User(Resource):

	@jwt_required()
	def get(self):
		current_user = get_jwt_identity()
		user = User.query.get(current_user)

		if user is None:
			return make_response(jsonify({"msg": 'Current user is not valid!'}, 401))
		records = User.query.all()

		data = [{
				'id': customer.id,
				'username': customer.username,
				'api_key': customer.api_key,
				'email': customer.email
		} for customer in records]
		return make_response(jsonify(data), 200)
