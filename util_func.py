from odoo.http import request

def make_response(code=200, message=None, data=None):
    """
    Create a HTTP Response for controller 
        :param message=None message string
        :param data=None data to return
        :param code=200 http status code
    """
    return {
        'status': code,
        'message': message,
        'data': data,
    }

def parse_request():
    # This can only be called inside controller method.
    # Parse and store request info {method, body, headers, token}
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
            return make_response(code=400, message='Could not parse input data.')
    return method, body, headers, token
