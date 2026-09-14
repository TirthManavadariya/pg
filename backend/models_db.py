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

        # If amenities is a list of strings, convert to structured format
        if amenities_data and isinstance(amenities_data[0], str):
            amenities_data = [{"name": a, "available": True} for a in amenities_data]
        elif not amenities_data:
            amenities_data = [
                {"name": "High-Speed Wi-Fi", "icon": "wifi", "available": bool(self.wifi)},
                {"name": "Air Conditioning", "icon": "ac", "available": bool(self.ac)},
                {"name": "Nutritious Meals", "icon": "food", "available": bool(self.food_included)},
                {"name": "Daily Housekeeping", "icon": "sparkles", "available": True},
                {"name": "Attached Washroom", "icon": "bath", "available": True},
                {"name": "24/7 Power Backup", "icon": "zap", "available": True},
                {"name": "Biometric / CCTV Security", "icon": "shield", "available": True},
                {"name": "RO Purified Water", "icon": "water", "available": True},
                {"name": "Washing Machine", "icon": "laundry", "available": True},
                {"name": "Geyser / Hot Water", "icon": "thermometer", "available": True},
            ]

        rules_data = {}
        if self.rules:
            try:
                rules_data = json.loads(self.rules)
            except Exception:
                rules_data = {}
        if not rules_data:
            rules_data = {
                "curfew": "No Curfew (Biometric 24/7 Access)",
                "visitors": "Allowed in common reception lounge till 9:00 PM",
                "deposit": "Only 1 Month Security Deposit (100% Refundable)",
                "notice_period": "30 Days Notice Period",
                "smoking_alcohol": "Strictly Non-Smoking inside private rooms"
            }

        photos_data = []
        if self.photos:
            try:
                photos_data = json.loads(self.photos)
            except Exception:
                photos_data = []

        # Fallback gallery if none provided
        sample_galleries = [
            [
                "/static/images/properties/bedroom_luxury_1.jpg",
                "/static/images/properties/living_lounge_1.jpg",
                "/static/images/properties/washroom_clean_1.jpg",
                "/static/images/properties/dining_kitchen_1.jpg"
            ],
            [
                "/static/images/properties/bedroom_modern_2.jpg",
                "/static/images/properties/living_lounge_2.jpg",
                "/static/images/properties/washroom_clean_2.jpg",
                "/static/images/properties/study_workspace_1.jpg"
            ],
            [
                "/static/images/properties/bedroom_cozy_3.jpg",
                "/static/images/properties/living_lounge_3.jpg",
                "/static/images/properties/balcony_view_1.jpg",
                "/static/images/properties/dining_kitchen_2.jpg"
            ],
            [
                "/static/images/properties/bedroom_double_4.jpg",
                "/static/images/properties/living_lounge_1.jpg",
                "/static/images/properties/washroom_clean_1.jpg",
                "/static/images/properties/study_workspace_2.jpg"
            ]
        ]
        h = sum(ord(c) for c in (self.id or self.name or 'pg'))
        fallback_gallery = sample_galleries[h % len(sample_galleries)]

        gallery = photos_data if (photos_data and len(photos_data) > 0) else fallback_gallery
        primary_image = gallery[0]

        # Dynamic Pricing Matrix from Live Room models
        pricing_matrix = {}
        for r in self.rooms:
            pricing_matrix[r.room_type] = r.rent_per_month
        
        base_rent = self.rent_monthly or 10000
        if "Double" not in pricing_matrix:
            pricing_matrix["Double"] = base_rent
        if "Single" not in pricing_matrix:
            pricing_matrix["Single"] = int(base_rent * 1.45 // 100 * 100)
        if "Triple" not in pricing_matrix:
            pricing_matrix["Triple"] = int(base_rent * 0.78 // 100 * 100)
        if "Dorm" not in pricing_matrix:
            pricing_matrix["Dorm"] = int(base_rent * 0.55 // 100 * 100)

        # Dynamic Badges
        badges = ["✓ Verified Property", "Zero Brokerage"]
        if (self.rating or 4.5) >= 4.5:
            badges.insert(0, "⚡ Fast Filling")
        if self.food_included:
            badges.append("Food Included")
        if self.ac:
            badges.append("AC Available")

        hub_types = ["Metro Station", "Tech Park", "Transit Hub", "Main Market", "University Campus"]
        nearest_hub = f"{round(0.4 + (h % 30) * 0.1, 1)} km from {hub_types[h % len(hub_types)]}"

        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'address': self.address or f"{self.locality}, {self.city}",
            'full_address': self.address or f"{self.locality}, {self.city} - 560001",
            'city': self.city,
            'locality': self.locality,
            'amenities': amenities_data,
            'rules': rules_data,
            'house_rules': rules_data,
            'photos': gallery,
            'image_url': primary_image,
            'gallery': gallery,
            'pricing_matrix': pricing_matrix,
            'badges': badges,
            'nearest_hub': nearest_hub,
            'lat': self.lat,
            'lng': self.lng,
            'gender': self.gender or 'Unisex',
            'rent_monthly': self.rent_monthly or base_rent,
            'sharing_type': self.sharing_type or 'Double',
            'ac': bool(self.ac),
            'wifi': bool(self.wifi),
            'food_included': bool(self.food_included),
            'food_type': self.food_type or 'Veg',
            'rating': round(float(self.rating or 4.5), 1),
            'reviews_count': int(self.reviews_count or 45),
            'description': self.description or f"{self.name} is a verified {self.sharing_type.lower() if self.sharing_type else 'co-living'} space located at {self.locality}, {self.city} offering modern fully furnished rooms with zero brokerage and premium amenities.",
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
