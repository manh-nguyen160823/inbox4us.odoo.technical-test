import jwt
from odoo import http
from functools import wraps
from odoo.http import request
from .auth_controller import SECRET_KEY
from .. import util_func
from datetime import datetime

# decorator handle request with jwt validation
def jwt_required(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        _, _, headers, token = util_func.parse_request()
        if "Authorization" in headers:
            token = headers["Authorization"].split(" ")[1]
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
            }
        
        if len(token.split('.')) != 3:
            return {
                "message": "Authentication Token is not valid!",
                "data": None,
            }
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if not data:
                return {
                    "message": "Invalid Authentication token!",
                    "data": None,
                }
        except Exception as e:
            return {
                "message": "Authentication Token failed.",
                "data": None,
                "error": str(e)
            }
        return fn(*args, **kwargs)
    return decorated

class BookingController(http.Controller):

    def get_customer(self, cid=None, token=None):
        customer_id = False
        HotelCustomer = request.env['hotel.customer'].sudo()
        if cid:
            customer_id = HotelCustomer.browse(int(cid)).exists()
        
        if not customer_id:
            try:
                data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                user_id = request.env['res.users'].sudo().browse(data['user_id']).exists()
                
                customer_id = HotelCustomer.create({
                    'name': user_id.name,
                    'email': user_id.email,
                    'phone': user_id.phone or '0977160823', # phone is required field.
                })
            except Exception as e:
                return util_func.make_response(code=403, message="Cannot get customer info to book hotel room!")
        
    @http.route('/api/booking', type='json', auth='public', methods=['POST'])
    # @validate_request - TODO: handle request validation - Nice to have
    # TODO: handle jwt token in the request
    @jwt_required
    def create_booking(self, **kwargs):
        # TODO: need to handle authentication access token
        # TODO: Implement booking creation logic
        # Note: need to check availability of the room
        method, body, headers, token = util_func.parse_request()
        
        if not body:
            return util_func.make_response(code=400, message='Invalid input content')
        if not body.get('room_id', ''):
            return util_func.make_response(code=400, message='Room ID cannot be empty!')
        else:
            try:
                int(body['room_id'])
                room_id = request.env['hotel.room'].sudo().browse(int(body['room_id'])).exists()
                if not room_id:
                    return util_func.make_response(code=403, message="Cannot find hotel room with ID: %s" % str(body['room_id']))
            except ValueError:
                return util_func.make_response(code=400, message="Room ID is not a valid value. It should be a positive integer!")
        if not body.get('checkin_date', ''):
            return util_func.make_response(code=400, message='Check-in Date is required!')
        else:
            try:
                datetime.strptime(body['checkin_date'], '%Y-%m-%d')
            except Exception as e:
                return util_func.make_response(code=400, message="Check-in Date is not a valid format '%Y-%m-%d'!")
        
        if not body.get('checkout_date', ''):
            return util_func.make_response(code=400, message='Check-out Date is required!')
        else:
            try:
                datetime.strptime(body['checkout_date'], '%Y-%m-%d')
            except Exception as e:
                return util_func.make_response(code=400, message="Check-out Date is not a valid format '%Y-%m-%d'!")
        
        self.get_customer(body.get('customer_id'), token)
        
        rid = body.get('room_id')
        cid = body.get('customer_id')
        check_in = body['checkin_date']
        check_out = body['checkout_date']
        
        request.env.cr.execute(
            """
            SELECT hr.id, hr.status, hb.id
              FROM hotel_room hr
              JOIN hotel_booking hb
                ON hb.room_id = hr.id 
               AND ((hb.check_in_date <= %s AND hb.check_out_date >= %s)
                   OR hr.status = 'maintenance')
             WHERE hr.id = %s;
            """,
            [check_out, check_in, rid]
        )
        row = request.env.cr.fetchone()
        if row:
            return util_func.make_response(code=404, message="Room ID: %s is not available right now." % rid)

        request.env['hotel.booking'].sudo().create({
            'room_id': rid,
            'customer_id': cid,
            'check_in_date': check_in,
            'check_out_date': check_out,
        })
        return util_func.make_response(code=200, message="Booking room ID: %s success." % rid)
