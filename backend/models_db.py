"""
backend/models_db.py
Persistent Database Models for Roomee Platform using SQLAlchemy.
Includes User, PGProperty, Room, Booking, and Payment.
"""
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'owner'
    college_name = db.Column(db.String(150), nullable=True)
    verified_status = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    properties = db.relationship('PGProperty', backref='owner', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'college_name': self.college_name,
            'verified_status': self.verified_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PGProperty(db.Model):
    __tablename__ = 'pg_properties'

    id = db.Column(db.String(50), primary_key=True)  # e.g., 'PG000001'
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300), nullable=True)
    city = db.Column(db.String(100), nullable=False, index=True)
    locality = db.Column(db.String(100), nullable=True, index=True)
    amenities = db.Column(db.Text, nullable=True)  # JSON string
    rules = db.Column(db.Text, nullable=True)      # JSON string
    photos = db.Column(db.Text, nullable=True)     # JSON string array
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    gender = db.Column(db.String(20), default='Unisex')
    rent_monthly = db.Column(db.Integer, default=10000)
    sharing_type = db.Column(db.String(50), default='Double')
    ac = db.Column(db.Boolean, default=False)
    wifi = db.Column(db.Boolean, default=True)
    food_included = db.Column(db.Boolean, default=False)
    food_type = db.Column(db.String(50), default='Veg')
    rating = db.Column(db.Float, default=4.5)
    reviews_count = db.Column(db.Integer, default=45)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    rooms = db.relationship('Room', backref='property', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='property', lazy=True)

    def to_dict(self):
        amenities_data = []
        if self.amenities:
            try:
                amenities_data = json.loads(self.amenities)
            except Exception:
                amenities_data = []

        rules_data = {}
        if self.rules:
            try:
                rules_data = json.loads(self.rules)
            except Exception:
                rules_data = {}

        photos_data = []
        if self.photos:
            try:
                photos_data = json.loads(self.photos)
            except Exception:
                photos_data = []

        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'locality': self.locality,
            'amenities': amenities_data,
            'rules': rules_data,
            'photos': photos_data,
            'lat': self.lat,
            'lng': self.lng,
            'gender': self.gender,
            'rent_monthly': self.rent_monthly,
            'sharing_type': self.sharing_type,
            'ac': self.ac,
            'wifi': self.wifi,
            'food_included': self.food_included,
            'food_type': self.food_type,
            'rating': self.rating,
            'reviews_count': self.reviews_count,
            'description': self.description,
            'rooms': [r.to_dict() for r in self.rooms]
        }


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    pg_id = db.Column(db.String(50), db.ForeignKey('pg_properties.id'), nullable=False, index=True)
    room_type = db.Column(db.String(50), nullable=False)  # 'Single', 'Double', 'Triple', 'Dorm'
    total_beds = db.Column(db.Integer, nullable=False, default=2)
    available_beds = db.Column(db.Integer, nullable=False, default=2)
    rent_per_month = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='room', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'pg_id': self.pg_id,
            'room_type': self.room_type,
            'total_beds': self.total_beds,
            'available_beds': self.available_beds,
            'rent_per_month': self.rent_per_month,
            'is_available': self.available_beds > 0
        }


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True, index=True)
    pg_id = db.Column(db.String(50), db.ForeignKey('pg_properties.id'), nullable=False, index=True)
    booking_type = db.Column(db.String(30), nullable=False)  # 'visit' or 'room_booking'
    visit_date = db.Column(db.String(50), nullable=True)
    visit_slot = db.Column(db.String(50), nullable=True)
    move_in_date = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='pending')  # 'pending', 'confirmed', 'rejected', 'cancelled'
    token_amount = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    payments = db.relationship('Payment', backref='booking', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        primary_photo = None
        if self.property and self.property.photos:
            try:
                photos_list = json.loads(self.property.photos)
                if photos_list:
                    primary_photo = photos_list[0]
            except Exception:
                pass

        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'Student',
            'user_email': self.user.email if self.user else None,
            'user_phone': self.user.phone if self.user else None,
            'college_name': self.user.college_name if self.user else None,
            'room_id': self.room_id,
            'room_type': self.room.room_type if self.room else None,
            'room_rent': self.room.rent_per_month if self.room else None,
            'pg_id': self.pg_id,
            'pg_name': self.property.name if self.property else 'Roomee Stay',
            'pg_city': self.property.city if self.property else '',
            'pg_locality': self.property.locality if self.property else '',
            'pg_image': primary_photo or '/static/images/properties/bedroom_luxury_1.jpg',
            'booking_type': self.booking_type,
            'visit_date': self.visit_date,
            'visit_slot': self.visit_slot,
            'move_in_date': self.move_in_date,
            'status': self.status,
            'token_amount': self.token_amount,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'payments': [p.to_dict() for p in self.payments]
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, index=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='created')  # 'created', 'paid', 'failed'
    payment_gateway = db.Column(db.String(50), default='Razorpay')       # 'Razorpay' or 'Stripe'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'status': self.status,
            'payment_gateway': self.payment_gateway,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
