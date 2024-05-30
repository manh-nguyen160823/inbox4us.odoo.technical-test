import json, logging, jwt, datetime, traceback

from odoo import http, _
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import werkzeug.utils

_logger = logging.getLogger(__name__)
regex = r"^[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"

SECRET_KEY = '5b7c284fc8e0b0e031'

class AuthController(http.Controller):
    
    def response(self, success=True, message=None, data=None, code=200):
        """
        Create a HTTP Response for controller 
            :param success=True indicate this response is successful or not
            :param message=None message string
            :param data=None data to return
            :param code=200 http status code
        """
        payload = json.dumps({
            'success': success,
            'message': message,
            'data': data,
        })

        return Response(payload, status=code, headers=[
            ('Content-Type', 'application/json'),
        ])
    
    def signup_email(self, values):
        user_sudo = request.env['res.users'].sudo().search([('login', '=', values.get('login'))])
        template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
        if user_sudo and template:
            template.sudo().with_context(
                lang=user_sudo.lang,
                auth_login=werkzeug.url_encode({'auth_login': user_sudo.email}),
            ).send_mail(user_sudo.id, force_send=True)
        
    def _prepare_signup_values(self, context):
        values = {key: context.get(key) for key in ('login', 'name', 'password')}
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang
        return values
        
    def do_signup(self, **content):
        """ Shared helper that creates a res.partner out of a token """
        values = self._prepare_signup_values(content)
        self._signup_with_values(content.get('token', ''), values)
        request.env.cr.commit()
        
    def _signup_with_values(self, token, values):
        try:
            login, password = request.env['res.users'].sudo().signup(values, token)
        except Exception:
            return self.response(success=False, code=400, message='Invalid input content')
        request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        pre_uid = request.session.authenticate(request.db, login, password)
        if not pre_uid:
            raise SignupError(_('Authentication Failed.'))
    
    @http.route('/api/auth/register', type='json', auth="none", methods=['POST'], cors='*', csrf=False)
    def register(self, **kw):
        # TODO: Implement user registration logic
        method, body, headers, token = self.parse_request()
        if not body:
            return self.response(success=False, code=400, message='Invalid input content')
            
        values = {key: body.get(key) for key in ('email', 'name', 'password')}
        self.do_signup(values)
        # Send an account creation confirmation email
        User = request.env['res.users']
        user_sudo = User.sudo().search(
            User._get_login_domain(values['email']), order=User._get_login_order(), limit=1
        )
        template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
        if user_sudo and template:
            template.sudo().send_mail(user_sudo.id, force_send=True)
            
        return self.response(False, 'Internal Server Error', None, 500)
    
    def parse_request(self):
        # This can only be called inside controller method.
        # Parse and store request info { method, body, headers, token }
        method = str(request.httprequest.method).lower()
        try:
            body = request.httprequest.json
        except Exception:
            body = {}
        headers = dict(list(request.httprequest.headers.items()))
        token = ''
        # checking headers
        if 'wsgi.input' in headers:
            del headers['wsgi.input']
        if 'wsgi.errors' in headers:
            del headers['wsgi.errors']
        if 'HTTP_AUTHORIZATION' in headers:
            headers['Authorization'] = headers['HTTP_AUTHORIZATION']
        if 'Authorization' in headers:
            try:
                # Bearer token_string
                token = headers['Authorization'].split(' ')[1]
            except Exception:
                pass

        return method, body, headers, token
    
    def validate_token(self, token, uid):
        return request.env["res.users.apikeys"]._check_credentials(scope='odoo.plugin.jwt', key=token) == uid
    
    def sign_token(payload):
        token = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        )
        return token.decode('utf-8')
    
    def create_new_access_token(self, payload):
          # Create a new token using the refresh token.
        try:
            get_user_id = payload['sub']
            get_user_lgn = payload['lgn']
            exp = datetime.datetime.utcnow() + datetime.timedelta(days=2)
            payload = {
                'exp': exp,
                'iat': datetime.datetime.utcnow(),
                'sub': get_user_id,
                'lgn': get_user_lgn,
            }
            token = self.sign_token(payload)
            self.save_token(token, get_user_id, exp)
            return token

        except Exception as ex:
            _logger.error(traceback.format_exc())
            raise
    
    @http.route('/api/auth/login', type='json', auth='none', methods=['POST'], cors='*', csrf=False)
    def login(self, **kw):
        # TODO: Implement user login logic and return JWT token
        method, body, headers, token = self.parse_request()
        user_id = request.env["res.users"].sudo().search([("login", "=", body['email'])], limit=1)
        
        if not (user_id and self.validate_token(token, user_id.id)):
            return self.response(success=False, code=403, data={"access_token": token}, message='Invalid Token')
        
        return self.response(data={"access_token": token}, message='Login success')
