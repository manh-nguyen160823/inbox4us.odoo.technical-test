## Inbox4us - Technical Test Requirements for Odoo Hotel Booking Module
### Overview
- Name module: hotel_management
- Dependencies are used in module:
  + module: auth_signup
  + package: jwt
- Use odoo version 16.0 community edition.
- Postman collection: send to your email

### Requirements
#### 1. Write REST API for Authentication using JWT

```
File: controllers/auth_controller.py
```
- Complete register portal user and return result.
- Check valid input data before signup.
```bash
curl -X POST http://localhost:8069/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@inbox4us.xyz",
    "password": "password"
    }'
```

- Check valid email and password user.
- Create a sign a new jwt token and return access token for the next request.
```bash
curl -X POST http://localhost:8069/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
      "email": "john@inbox4us.xyz",
      "password": "password"
    }'
```

#### 2. Write API for Making a Booking
```
File: controllers/booking_controller.py
```

- Complete implement an endpoint to create a new booking.
- Validate correct access token before process a booking hotel room.
- Check valid input data before make a booking:
  + Customer: check valid ID, if not exist create new customer with current user (get via access token).
  + Hotel Room: check valid ID, if not exist raise a notice.
  + Check-in, Check-out: check valid format, check available room with request range date.
```bash
curl -X POST http://localhost:8069/api/booking \
  -H "Content-Type: application/json
  --header 'Authorization: Bearer <REPLACE_ACCESSTOKEN>' \
  -d '{
    "room_id": 1,
    "customer_id": 1,
    "checkin_date": "2022-01-01",
    "checkout_date": "2022-01-05"
  }'
```