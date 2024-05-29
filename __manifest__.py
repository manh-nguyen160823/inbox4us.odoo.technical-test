{
    'name': 'Inbox4us Hotel Booking Management',
    'version': '1.0',
    'category': 'Hotel Management',
    'summary': 'Manage hotel room bookings and customers',
    'depends': ['base'],
    'installable': True,
    'application': True,
    'data': [
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'views/hotel_menu_views.xml',
        'views/hotel_booking_views.xml',
        'views/hotel_customer_views.xml',
        'views/hotel_room_views.xml',
    ],
}