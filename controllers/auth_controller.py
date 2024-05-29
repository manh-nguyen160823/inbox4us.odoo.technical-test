
import functools
import json
import logging
import jwt

import werkzeug.utils
from werkzeug.exceptions import BadRequest

from odoo import api, http, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied
from odoo.http import request, Response


from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

SECRET_KEY = 'your_secret_key_here'

class AuthController(http.Controller):
    
    def generate_jwt(payload, lifetime=None):
        # Generates a new JWT token, wrapping information provided by payload (dict)
        # Lifetime describes (in minutes) how much time the token will be valid
        if lifetime:
            payload['exp'] = (datetime.now() + timedelta(minutes=lifetime)).timestamp()
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    def decode_jwt(token):
        # Tries to retrieve payload information inside of a existent JWT token (string)
        # Will throw an error if the token is invalid (expired or inconsistent)
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    
    def authenticate(email, password):
        if email == 'john@inbox4us.xyz' and password == 'password':
            return {
                'username': 'admin',
                'email': 'john@inbox4us.xyz',
                'roles': ['admin', 'user']
            }
        else:
            return False

    @http.route('/api/register', type='json', auth="none", methods=['POST'], cors='*', csrf=False)
    def register(self, **kwargs):
        # TODO: Implement user registration logic
        pass

    @http.route('/api/login', type='json', auth='none', methods=['POST'], cors='*', csrf=False)
    def login(self, **kwargs):
        # TODO: Implement user login logic and return JWT token
    

    
