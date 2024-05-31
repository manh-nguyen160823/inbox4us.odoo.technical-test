import jwt
from odoo import SUPERUSER_ID, http, _
from odoo.http import request
from .. import util_func

SECRET_KEY = '0ea15f34168de1959fc94762dffa6ad60080ec9b'

class AuthController(http.Controller):
    
    def _prepare_user_values(self, values):
        results = {key: values.get(key) for key in ('email', 'name', 'password')}
        if not results.get('login', ''):
            results['login'] = values['email']
            
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            results['lang'] = lang
        return results

    def _signup_portal_user_with_values(self, token, values):
        # have to use with_user(SUPERUSER_ID) cause several fields need default values,
        # like company_id get from self.env.user
        login, password = request.env['res.users'].with_user(SUPERUSER_ID).sudo().signup(values, token)
        request.env.cr.commit()
        uid = request.session.authenticate(request.db, login, password)
        if not uid:
            return util_func.make_response(code=400, message='Create portal user failed.')
        
    def create_portal_user(self, values):
        values = self._prepare_user_values(values)
        self._signup_portal_user_with_values(values.get('token', ''), values)
        request.env.cr.commit()
    
    @http.route('/api/auth/register', type='json', auth="none", methods=['POST'], cors='*', csrf=False)
    def register(self, **kw):
        # TODO: Implement user registration logic
        _, body, _, _ = util_func.parse_request()
        if not body:
            return util_func.make_response(code=400, message='Invalid input content')
        if not body.get('email', ''):
            return util_func.make_response(code=400, message='Invalid email address')
        if not body.get('name', ''):
            return util_func.make_response(code=400, message='Name cannot be empty')
        if not body.get('password', ''):
            return util_func.make_response(code=400, message='Password cannot be empty')

        User = request.env['res.users'].sudo()
        existed_user = User.search(User._get_login_domain(body.get('email')), order=User._get_login_order(), limit=1)
        if existed_user:
            return util_func.make_response(code=400, message='Email has been signed up.')
                
        self.create_portal_user({
            'email': body['email'],
            'name': body['name'],
            'password': body['password'],
        })
        request.env.cr.commit()
        return util_func.make_response(data={'login': body['email']}, message='Create user success.')
    
    def sign_token(self, uid):
        return jwt.encode(
            {"user_id": uid},
            SECRET_KEY,
            algorithm='HS256'
        )
    
    @http.route('/api/auth/login', type='json', auth='none', methods=['POST'], cors='*', csrf=False)
    def login(self, **kw):
        # TODO: Implement user login logic and return JWT token
        method, body, headers, token = util_func.parse_request()
        uid = request.session.authenticate(request.db, body.get('email', ''), body.get('password', ''))
        if not uid:
            return util_func.make_response(code=403, data={"access_token": token}, message='Invalid email or password.')
        
        # set new token for user
        token = self.sign_token(uid)
        return util_func.make_response(data={"UID": uid, "access_token": token}, message='Successfully fetched auth token.')
