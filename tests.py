import json
from unittest import TestCase, mock
from flask import Flask
from flask_jwt_extended import create_access_token
from app import app, db
from models.user import User


class TestCreateUser(TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_user(self):
        with app.test_client() as client:
            # create a new user
            data = {
                'username': 'testuser',
                'email': 'testuser@example.com',
                'password': 'testpassword'
            }
            response = client.post('/api/users', data=json.dumps(data), content_type='application/json')
            self.assertEqual(response.status_code, 200)

            # check if the user was created in the database
            user = User.query.filter_by(username=data['username']).first()
            self.assertIsNotNone(user)

            # check if the user password was correctly hashed
            self.assertTrue(user.check_password(data['password']))

