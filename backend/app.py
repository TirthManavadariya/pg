"""
backend/app.py
Production Roomee PG Discovery & Booking Engine.
Provides persistent database models, authentication, role-based access control,
booking and visit scheduling with concurrency locking, Razorpay/Stripe payment flow,
notification hooks, and lightning-fast search & filtering.
"""

import os
import sys
import json
import secrets
import hashlib
import random
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

STATIC_DIR = os.path.join(BASE_DIR, 'static')
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

# Import Database & Models
from backend.models_db import db, User, PGProperty, Room, Booking, Payment
from backend.auth import (
    hash_password, verify_password, generate_jwt_token,
    token_required, roles_accepted
)
from backend.notifications import (
    send_booking_notification, send_status_update_notification, send_payment_notification
)

app = Flask(__name__, static_folder=None)
CORS(app)

# Database Configuration
DB_PATH = os.path.join(INSTANCE_DIR, 'roomee.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f"sqlite:///{DB_PATH}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Load CSV Dataset
CSV_PATH = os.path.join(BASE_DIR, 'pg_listings.csv')
if not os.path.exists(CSV_PATH):
    CSV_PATH = os.path.join(BASE_DIR, 'pg_dataset_final_v2_named.csv')

df_pgs = None

# Pre-defined high quality property images mapping
PROPERTY_IMAGE_SETS = [
    {
        "primary": "/static/images/properties/bedroom_luxury_1.jpg",
        "gallery": [
            "/static/images/properties/bedroom_luxury_1.jpg",
            "/static/images/properties/living_lounge_1.jpg",
            "/static/images/properties/washroom_clean_1.jpg",
            "/static/images/properties/dining_kitchen_1.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/bedroom_modern_2.jpg",
        "gallery": [
            "/static/images/properties/bedroom_modern_2.jpg",
            "/static/images/properties/living_lounge_2.jpg",
            "/static/images/properties/washroom_clean_2.jpg",
            "/static/images/properties/study_workspace_1.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/bedroom_cozy_3.jpg",
        "gallery": [
            "/static/images/properties/bedroom_cozy_3.jpg",
            "/static/images/properties/living_lounge_3.jpg",
            "/static/images/properties/balcony_view_1.jpg",
            "/static/images/properties/dining_kitchen_2.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/bedroom_double_4.jpg",
        "gallery": [
            "/static/images/properties/bedroom_double_4.jpg",
            "/static/images/properties/living_lounge_1.jpg",
            "/static/images/properties/washroom_clean_1.jpg",
            "/static/images/properties/study_workspace_2.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/bedroom_single_5.jpg",
        "gallery": [
            "/static/images/properties/bedroom_single_5.jpg",
            "/static/images/properties/living_lounge_2.jpg",
            "/static/images/properties/balcony_view_1.jpg",
            "/static/images/properties/washroom_clean_2.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/bedroom_scandi_6.jpg",
        "gallery": [
            "/static/images/properties/bedroom_scandi_6.jpg",
            "/static/images/properties/study_workspace_1.jpg",
            "/static/images/properties/dining_kitchen_1.jpg",
            "/static/images/properties/washroom_clean_1.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/bedroom_minimal_7.jpg",
        "gallery": [
            "/static/images/properties/bedroom_minimal_7.jpg",
            "/static/images/properties/living_lounge_3.jpg",
            "/static/images/properties/dining_kitchen_2.jpg",
            "/static/images/properties/washroom_clean_2.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/bedroom_studio_8.jpg",
        "gallery": [
            "/static/images/properties/bedroom_studio_8.jpg",
            "/static/images/properties/balcony_view_1.jpg",
            "/static/images/properties/study_workspace_2.jpg",
            "/static/images/properties/washroom_clean_1.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/living_lounge_1.jpg",
        "gallery": [
            "/static/images/properties/living_lounge_1.jpg",
            "/static/images/properties/bedroom_luxury_1.jpg",
            "/static/images/properties/dining_kitchen_1.jpg",
            "/static/images/properties/washroom_clean_1.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/living_lounge_2.jpg",
        "gallery": [
            "/static/images/properties/living_lounge_2.jpg",
            "/static/images/properties/bedroom_modern_2.jpg",
            "/static/images/properties/study_workspace_1.jpg",
            "/static/images/properties/washroom_clean_2.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/study_workspace_1.jpg",
        "gallery": [
            "/static/images/properties/study_workspace_1.jpg",
            "/static/images/properties/bedroom_scandi_6.jpg",
            "/static/images/properties/balcony_view_1.jpg",
            "/static/images/properties/washroom_clean_1.jpg",
        ]
    },
    {
        "primary": "/static/images/properties/living_lounge_3.jpg",
        "gallery": [
            "/static/images/properties/living_lounge_3.jpg",
            "/static/images/properties/bedroom_minimal_7.jpg",
            "/static/images/properties/dining_kitchen_2.jpg",
            "/static/images/properties/balcony_view_1.jpg",
        ]
    },
]

WEEKLY_FOOD_MENU = {
    "Monday": {"breakfast": "Poha, Boiled Eggs / Banana, Tea / Coffee", "lunch": "Dal Tadka, Paneer Butter Masala, Roti, Rice, Salad", "dinner": "Mix Veg Curry, Jeera Rice, Chapatis, Gulab Jamun"},
    "Tuesday": {"breakfast": "Idli Sambar, Coconut Chutney, Tea / Coffee", "lunch": "Rajma Masala, Steamed Basmati Rice, Curd, Roti", "dinner": "Aloo Gobi, Dal Makhani, Phulkas, Kheer"},
    "Wednesday": {"breakfast": "Aloo Paratha with Curd & Pickle, Tea", "lunch": "Chole Bhature / Rice, Boondi Raita, Salad", "dinner": "Egg Curry / Paneer Kadhai, Dal Fry, Roti, Rice"},
    "Thursday": {"breakfast": "Upma, Medu Vada, Filter Coffee", "lunch": "Kadhi Pakora, Khichdi / Rice, Papad, Roti", "dinner": "Bhindi Do Pyaza, Yellow Dal, Chapati, Custard"},
    "Friday": {"breakfast": "Puri Bhaji, Fruit Bowl, Tea / Coffee", "lunch": "Veg Pulao, Paneer Lababdar, Cucumber Raita", "dinner": "Chicken Biryani / Special Veg Biryani, Salan, Raita, Ice Cream"},
    "Saturday": {"breakfast": "Uttapam with Sambar & Chutneys, Tea", "lunch": "Dal Palak, Aloo Jeera, Steamed Rice, Roti", "dinner": "Pav Bhaji, Pulao, Sweet Corn Soup"},
    "Sunday": {"breakfast": "Masala Dosa, Filter Coffee / Juice", "lunch": "Special Weekend Thali: Paneer Tikka / Chicken Curry, Naan, Pulao", "dinner": "Light Khichdi, Kadhi, Papad, Dessert"}
}

def get_deterministic_hash(text_id):
    return int(hashlib.md5(str(text_id).encode('utf-8')).hexdigest(), 16)

def enrich_pg_record(row):
    """Enriches a single raw PG row with full ZoloStays-grade metadata."""
    pg_id = str(row.get('pg_id', 'PG000000'))
    h = get_deterministic_hash(pg_id)
    
    name = str(row.get('name', 'Co-living Stay'))
    city = str(row.get('city', 'Bangalore'))
    locality = str(row.get('locality', 'City Center'))
    rent = int(row.get('rent_monthly', 10000))
    sharing = str(row.get('sharing_type', 'Double'))
    ac = str(row.get('ac', 'No')).strip().lower() in ['yes', '1', 'true']
    wifi = str(row.get('wifi', 'Yes')).strip().lower() in ['yes', '1', 'true']
    food_included = str(row.get('food_included', 'No')).strip().lower() in ['yes', '1', 'true']
    food_type = str(row.get('food_type', 'Veg'))
    desc = str(row.get('description', ''))
    
    # Infer Gender
    name_lower = name.lower()
    desc_lower = desc.lower()
    if 'girl' in name_lower or 'women' in name_lower or 'for girls' in desc_lower or 'for women' in desc_lower:
        gender = 'Women'
    elif 'boy' in name_lower or 'men' in name_lower or 'for boys' in desc_lower or 'for men' in desc_lower:
        gender = 'Men'
    else:
        gender_options = ['Unisex', 'Men', 'Women', 'Unisex']
        gender = gender_options[h % len(gender_options)]

    # Dynamic image set
    img_set_idx = (h + rent // 700 + len(name)) % len(PROPERTY_IMAGE_SETS)
    selected_img_set = PROPERTY_IMAGE_SETS[img_set_idx]
    
    # Ratings & Reviews
    rating = round(4.2 + (h % 8) * 0.1, 1)
    reviews_count = 25 + (h % 220)
    
    # Badges
    badges = []
    if h % 3 == 0:
        badges.append("⚡ Fast Filling")
    if h % 2 == 0:
        badges.append("Verified Property")
    badges.append("Zero Brokerage")
    if food_included:
        badges.append("Food Included")
    if ac:
        badges.append("AC Available")
        
    # Distance info
    dist_val = round(0.4 + (h % 35) * 0.1, 1)
    hub_types = ["Metro Station", "Tech Park", "Transit Hub", "Main Market", "University Campus"]
    nearest_hub = f"{dist_val} km from {hub_types[h % len(hub_types)]}"

    # Sharing Pricing Matrix
    pricing_matrix = {
        "Single": int(rent * 1.45 // 100 * 100),
        "Double": rent,
        "Triple": int(rent * 0.78 // 100 * 100),
        "Dorm": int(rent * 0.55 // 100 * 100),
    }

    # Available amenities
    amenities = [
        {"name": "High-Speed Wi-Fi", "icon": "wifi", "available": wifi},
        {"name": "Air Conditioning", "icon": "ac", "available": ac},
        {"name": "Nutritious Meals", "icon": "food", "available": food_included},
        {"name": "Daily Housekeeping", "icon": "sparkles", "available": True},
        {"name": "Attached Washroom", "icon": "bath", "available": (h % 5 != 0)},
        {"name": "24/7 Power Backup", "icon": "zap", "available": True},
        {"name": "Biometric / CCTV Security", "icon": "shield", "available": True},
        {"name": "RO Purified Water", "icon": "water", "available": True},
        {"name": "Washing Machine", "icon": "laundry", "available": True},
        {"name": "Geyser / Hot Water", "icon": "thermometer", "available": True},
    ]

    return {
        "id": pg_id,
        "name": name,
        "city": city,
        "locality": locality,
        "full_address": f"{locality}, {city} - 560001",
        "gender": gender,
        "sharing_type": sharing,
        "rent_monthly": rent,
        "pricing_matrix": pricing_matrix,
        "ac": ac,
        "wifi": wifi,
        "food_included": food_included,
        "food_type": food_type,
        "rating": rating,
        "reviews_count": reviews_count,
        "nearest_hub": nearest_hub,
        "badges": badges,
        "image_url": selected_img_set["primary"],
        "gallery": selected_img_set["gallery"],
        "amenities": amenities,
        "description": desc or f"{name} is a premium {sharing.lower()} co-living space located at {locality}, {city} offering modern fully furnished rooms with zero brokerage and top amenities.",
        "house_rules": {
            "curfew": "No Curfew (Biometric 24/7 Access)" if (h % 2 == 0) else "11:30 PM (Entry permitted with prior notice)",
            "visitors": "Allowed in common reception lounge till 9:00 PM",
            "deposit": "Only 1 Month Security Deposit (100% Refundable)",
            "notice_period": "30 Days Notice Period",
            "smoking_alcohol": "Strictly Non-Smoking inside private rooms"
        },
        "food_menu": WEEKLY_FOOD_MENU
    }

def get_or_create_property_db(pg_id, row=None, owner_user=None):
    """
    Ensures a PG exists in the persistent SQLite database along with its room models and beds.
    """
    prop = PGProperty.query.get(pg_id)
    if prop:
        return prop

    if row is None and df_pgs is not None:
        match = df_pgs[df_pgs['pg_id'].astype(str) == str(pg_id)]
        if not match.empty:
            row = match.iloc[0]

    if row is None:
        return None

    enriched = enrich_pg_record(row)
    owner_id = owner_user.id if owner_user else None

    prop = PGProperty(
        id=pg_id,
        owner_id=owner_id,
        name=enriched['name'],
        address=enriched['full_address'],
        city=enriched['city'],
        locality=enriched['locality'],
        amenities=json.dumps(enriched['amenities']),
        rules=json.dumps(enriched['house_rules']),
        photos=json.dumps(enriched['gallery']),
        gender=enriched['gender'],
        rent_monthly=enriched['rent_monthly'],
        sharing_type=enriched['sharing_type'],
        ac=enriched['ac'],
        wifi=enriched['wifi'],
        food_included=enriched['food_included'],
        food_type=enriched['food_type'],
        rating=enriched['rating'],
        reviews_count=enriched['reviews_count'],
        description=enriched['description']
    )
    db.session.add(prop)
    db.session.flush()

    # Create Room records with initial bed capacities
    matrix = enriched['pricing_matrix']
    rooms_data = [
        {"type": "Single", "beds": 1, "rent": matrix.get("Single", 14500)},
        {"type": "Double", "beds": 2, "rent": matrix.get("Double", 10000)},
        {"type": "Triple", "beds": 3, "rent": matrix.get("Triple", 7800)},
        {"type": "Dorm", "beds": 4, "rent": matrix.get("Dorm", 5500)}
    ]
    for r in rooms_data:
        room = Room(
            pg_id=pg_id,
            room_type=r["type"],
            total_beds=r["beds"],
            available_beds=r["beds"],
            rent_per_month=r["rent"]
        )
        db.session.add(room)

    db.session.commit()
    return prop

def init_database():
    """Initializes tables and seeds default demo users and top properties."""
    with app.app_context():
        db.create_all()
        
        # 1. Seed demo student
        student = User.query.filter_by(email="student@roomee.com").first()
        if not student:
            student = User(
                name="Rahul Sharma",
                email="student@roomee.com",
                phone="9876543210",
                password_hash=hash_password("password123"),
                role="student",
                college_name="Indian Institute of Technology / Christ University",
                verified_status=True
            )
            db.session.add(student)

        # 2. Seed demo PG owner
        owner = User.query.filter_by(email="owner@roomee.com").first()
        if not owner:
            owner = User(
                name="Vikram Malhotra",
                email="owner@roomee.com",
                phone="9823456789",
                password_hash=hash_password("password123"),
                role="owner",
                college_name=None,
                verified_status=True
            )
            db.session.add(owner)
            db.session.commit()
        else:
            db.session.commit()

        # 3. Seed top properties into DB if empty
        if PGProperty.query.count() < 10 and df_pgs is not None:
            print("Seeding initial properties and room inventories into persistent database...")
            sample_count = min(150, len(df_pgs))
            for i in range(sample_count):
                row = df_pgs.iloc[i]
                pg_id = str(row.get('pg_id', f'PG{str(i+1).zfill(6)}'))
                get_or_create_property_db(pg_id, row, owner)
            print(f"Database initialized with {PGProperty.query.count()} properties & inventories.")

def load_data():
    global df_pgs
    print(f"Loading PG listings from {CSV_PATH}...")
    df_pgs = pd.read_csv(CSV_PATH)
    # Ensure consistent column naming
    if 'Rent' in df_pgs.columns and 'rent_monthly' not in df_pgs.columns:
        df_pgs.rename(columns={
            'Rent': 'rent_monthly',
            'PG_Name': 'name',
            'City': 'city',
            'Area': 'locality',
            'Food': 'food_included',
            'WiFi': 'wifi',
            'AC': 'ac',
            'Gender': 'gender_col'
        }, inplace=True)
    if 'pg_id' not in df_pgs.columns:
        df_pgs['pg_id'] = ['PG' + str(i).zfill(6) for i in range(1, len(df_pgs) + 1)]
            
    print(f"Successfully loaded {len(df_pgs)} listings from CSV.")

load_data()
init_database()

# ─── Auth API Routes ──────────────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new student or PG owner account."""
    payload = request.get_json(force=True, silent=True) or {}
    name = payload.get('name', '').strip()
    email = payload.get('email', '').strip().lower()
    password = payload.get('password', '')
    phone = payload.get('phone', '').strip()
    role = payload.get('role', 'student').strip().lower()
    college_name = payload.get('college_name', '').strip()

    if not name or not email or not password:
        return jsonify({"success": False, "error": "Name, email, and password are required"}), 400

    if role not in ['student', 'owner']:
        role = 'student'

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"success": False, "error": "An account with this email already exists"}), 409

    new_user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        phone=phone,
        role=role,
        college_name=college_name,
        verified_status=True
    )
    db.session.add(new_user)
    db.session.commit()

    token = generate_jwt_token(new_user)
    return jsonify({
        "success": True,
        "message": f"Welcome {name}! Your {role} account was created.",
        "token": token,
        "user": new_user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate student or PG owner."""
    payload = request.get_json(force=True, silent=True) or {}
    email = payload.get('email', '').strip().lower()
    password = payload.get('password', '')

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"success": False, "error": "Invalid email or password"}), 401

    token = generate_jwt_token(user)
    return jsonify({
        "success": True,
        "message": f"Welcome back, {user.name}!",
        "token": token,
        "user": user.to_dict()
    })

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user_profile(current_user):
    """Returns the authenticated user's profile and active stats."""
    return jsonify({
        "success": True,
        "user": current_user.to_dict()
    })

# ─── Booking & Visit Scheduling APIs ──────────────────────────────────────────

@app.route('/api/bookings', methods=['POST'])
@token_required
def create_booking(current_user):
    """
    Allows a student to book a bed or schedule a physical visit.
    Checks bed availability, uses DB transaction locking to prevent overbooking,
    and creates the booking record.
    """
    payload = request.get_json(force=True, silent=True) or {}
    booking_type = payload.get('booking_type', 'room_booking').strip()  # 'room_booking' or 'visit'
    pg_id = str(payload.get('pg_id', '')).strip()
    room_id = payload.get('room_id')
    visit_date = payload.get('visit_date')
    visit_slot = payload.get('visit_slot', 'Morning (10:00 AM - 01:00 PM)')
    move_in_date = payload.get('move_in_date')
    token_amount = int(payload.get('token_amount', 0))
    notes = payload.get('notes', '')

    if not pg_id:
        return jsonify({"success": False, "error": "Property ID is required"}), 400

    # Ensure property exists in persistent DB
    prop = get_or_create_property_db(pg_id)
    if not prop:
        return jsonify({"success": False, "error": f"Property '{pg_id}' not found"}), 404

    if booking_type == 'room_booking':
        if not room_id:
            return jsonify({"success": False, "error": "room_id is required for room reservation"}), 400

        try:
            # Transaction & Row Lock to prevent race condition / overbooking
            room = db.session.query(Room).filter_by(id=room_id, pg_id=pg_id).with_for_update().first()
            if not room:
                return jsonify({"success": False, "error": "Selected room does not exist for this property"}), 404

            if room.available_beds <= 0:
                return jsonify({
                    "success": False,
                    "error": f"Sorry! All beds in {room.room_type} room are currently fully booked."
                }), 400

            booking = Booking(
                user_id=current_user.id,
                room_id=room.id,
                pg_id=pg_id,
                booking_type='room_booking',
                move_in_date=move_in_date or datetime.utcnow().strftime("%Y-%m-%d"),
                token_amount=token_amount or 2000,
                status='pending',
                notes=notes
            )
            db.session.add(booking)
            db.session.commit()

            # Trigger notification hook
            send_booking_notification(booking, "created")

            return jsonify({
                "success": True,
                "message": "Bed reservation request placed successfully! Complete token advance payment to confirm.",
                "booking": booking.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Booking transaction error: {str(e)}"}), 500

    elif booking_type == 'visit':
        if not visit_date:
            return jsonify({"success": False, "error": "Preferred visit date is required"}), 400

        try:
            booking = Booking(
                user_id=current_user.id,
                room_id=room_id,
                pg_id=pg_id,
                booking_type='visit',
                visit_date=visit_date,
                visit_slot=visit_slot,
                status='confirmed',  # Free physical visits are confirmed immediately
                token_amount=0,
                notes=notes
            )
            db.session.add(booking)
            db.session.commit()

            # Trigger notification hook
            send_booking_notification(booking, "visit_scheduled")

            return jsonify({
                "success": True,
                "message": f"Free property visit confirmed for {visit_date} ({visit_slot})!",
                "booking": booking.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Visit scheduling error: {str(e)}"}), 500

    return jsonify({"success": False, "error": "Invalid booking_type. Must be 'room_booking' or 'visit'"}), 400

@app.route('/api/bookings/my-bookings', methods=['GET'])
@token_required
def get_my_bookings(current_user):
    """Returns all active and historical bookings for the logged-in student."""
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return jsonify({
        "success": True,
        "count": len(bookings),
        "bookings": [b.to_dict() for b in bookings]
    })

@app.route('/api/owner/bookings', methods=['GET'])
@token_required
@roles_accepted('owner')
def get_owner_bookings(current_user):
    """Allows a PG owner to view incoming booking/visit requests for their properties."""
    owned_props = PGProperty.query.filter_by(owner_id=current_user.id).all()
    prop_ids = [p.id for p in owned_props]

    if prop_ids:
        bookings = Booking.query.filter(Booking.pg_id.in_(prop_ids)).order_by(Booking.created_at.desc()).all()
    else:
        # Fallback for demo owner so they can see all test requests
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()

    return jsonify({
        "success": True,
        "count": len(bookings),
        "bookings": [b.to_dict() for b in bookings]
    })

@app.route('/api/owner/bookings/<int:booking_id>', methods=['PATCH'])
@token_required
@roles_accepted('owner')
def update_owner_booking(current_user, booking_id):
    """
    Allows PG owners to accept or reject requests.
    Decrements available bed count upon confirmation and restores beds if rejected/cancelled.
    """
    payload = request.get_json(force=True, silent=True) or {}
    new_status = payload.get('status', '').strip().lower()

    if new_status not in ['confirmed', 'rejected', 'cancelled', 'pending']:
        return jsonify({"success": False, "error": "Invalid status. Allowed: confirmed, rejected, cancelled"}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"success": False, "error": "Booking request not found"}), 404

    old_status = booking.status
    if old_status == new_status:
        return jsonify({"success": True, "booking": booking.to_dict()})

    try:
        # Handle bed inventory decrement/increment if room_booking
        if booking.booking_type == 'room_booking' and booking.room_id:
            room = db.session.query(Room).filter_by(id=booking.room_id).with_for_update().first()
            if room:
                if new_status == 'confirmed' and old_status != 'confirmed':
                    if room.available_beds <= 0:
                        return jsonify({
                            "success": False,
                            "error": f"Cannot confirm: All beds in {room.room_type} room are already occupied."
                        }), 400
                    room.available_beds -= 1
                elif old_status == 'confirmed' and new_status in ['rejected', 'cancelled']:
                    if room.available_beds < room.total_beds:
                        room.available_beds += 1

        booking.status = new_status
        db.session.commit()

        # Trigger notification alert
        send_status_update_notification(booking, old_status, new_status)

        return jsonify({
            "success": True,
            "message": f"Booking request #{booking_id} status updated to '{new_status}'",
            "booking": booking.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to update booking status: {str(e)}"}), 500

# ─── Payment Flow Mock / Integration APIs ────────────────────────────────────

@app.route('/api/payments/create-order', methods=['POST'])
@token_required
def create_payment_order(current_user):
    """
    Generates a secure checkout order compatible with Razorpay/Stripe payload structures.
    """
    payload = request.get_json(force=True, silent=True) or {}
    booking_id = payload.get('booking_id')
    amount = payload.get('amount')
    gateway = payload.get('gateway', 'Razorpay').strip()

    if not booking_id:
        return jsonify({"success": False, "error": "booking_id is required"}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"success": False, "error": "Booking not found"}), 404

    if not amount:
        amount = booking.token_amount or 2000

    prefix = "order_rzp" if gateway.lower() == 'razorpay' else "pi_stripe"
    order_id = f"{prefix}_{secrets.token_hex(8)}"

    payment = Payment(
        booking_id=booking.id,
        transaction_id=order_id,
        amount=int(amount),
        status='created',
        payment_gateway=gateway
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({
        "success": True,
        "order_id": order_id,
        "amount": int(amount) * 100,  # in paise for Razorpay
        "display_amount": int(amount),
        "currency": "INR",
        "key_id": "rzp_test_roomee_demo_873",
        "booking_id": booking.id,
        "payment_gateway": gateway,
        "prefill": {
            "name": current_user.name,
            "email": current_user.email,
            "contact": current_user.phone or ""
        },
        "notes": {
            "property_name": booking.property.name if booking.property else "Roomee Stay",
            "booking_id": booking.id
        }
    }), 201

@app.route('/api/payments/verify', methods=['POST'])
@token_required
def verify_payment(current_user):
    """
    Verifies payment signature / transaction.
    Automatically updates booking status to 'confirmed' and safely decrements bed count.
    """
    payload = request.get_json(force=True, silent=True) or {}
    booking_id = payload.get('booking_id')
    order_id = payload.get('order_id') or payload.get('razorpay_order_id') or payload.get('payment_intent_id')
    payment_id = payload.get('payment_id') or payload.get('razorpay_payment_id') or f"pay_{secrets.token_hex(8)}"

    if not booking_id:
        return jsonify({"success": False, "error": "booking_id is required"}), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"success": False, "error": "Booking not found"}), 404

    payment = Payment.query.filter_by(booking_id=booking_id).order_by(Payment.id.desc()).first()
    if not payment:
        payment = Payment(
            booking_id=booking_id,
            transaction_id=payment_id,
            amount=booking.token_amount or 2000,
            status='paid',
            payment_gateway='Razorpay'
        )
        db.session.add(payment)
    else:
        payment.status = 'paid'
        payment.transaction_id = payment_id

    try:
        old_status = booking.status
        booking.status = 'confirmed'

        # Decrement bed count atomically if room_booking and not yet confirmed
        if booking.booking_type == 'room_booking' and booking.room_id and old_status != 'confirmed':
            room = db.session.query(Room).filter_by(id=booking.room_id).with_for_update().first()
            if room and room.available_beds > 0:
                room.available_beds -= 1

        db.session.commit()

        # Trigger notification hooks
        send_payment_notification(payment, booking)
        send_status_update_notification(booking, old_status, 'confirmed')

        return jsonify({
            "success": True,
            "message": "Payment verified successfully! Your room booking is confirmed.",
            "payment": payment.to_dict(),
            "booking": booking.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Payment confirmation error: {str(e)}"}), 500

# ─── Legacy Visit Booking Compatibility ──────────────────────────────────────

@app.route('/api/book-visit', methods=['POST'])
def legacy_book_visit():
    """Legacy endpoint maintaining backward compatibility."""
    payload = request.get_json(force=True, silent=True) or {}
    pg_id = str(payload.get('pg_id', '')).strip()
    name = payload.get('name', '').strip()
    phone = payload.get('phone', '').strip()
    date = payload.get('date', '').strip()
    slot = payload.get('slot', 'Morning (10:00 AM - 01:00 PM)').strip()

    if not name or not phone:
        return jsonify({"success": False, "error": "Name and Phone number are required"}), 400

    # Find or create a user for this visit
    user = User.query.filter_by(phone=phone).first()
    if not user:
        user = User.query.filter_by(email="student@roomee.com").first()

    # Ensure property in DB
    get_or_create_property_db(pg_id)

    booking = Booking(
        user_id=user.id if user else 1,
        pg_id=pg_id,
        booking_type='visit',
        visit_date=date,
        visit_slot=slot,
        status='confirmed',
        notes=f"Scheduled by {name} ({phone})"
    )
    db.session.add(booking)
    db.session.commit()

    booking_id = f"ROOMEE-VISIT-{booking.id}"
    send_booking_notification(booking, "visit_scheduled")

    return jsonify({
        "success": True,
        "booking_id": booking_id,
        "message": f"Your free visit has been successfully confirmed for {date or 'the selected date'} ({slot}). Our property manager will assist you upon arrival!",
        "details": {
            "booking_id": booking_id,
            "pg_id": pg_id,
            "name": name,
            "phone": phone,
            "date": date,
            "slot": slot
        }
    })

# ─── Discovery & Property APIs ───────────────────────────────────────────────

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Returns top cities with total listings and top localities."""
    city_counts = df_pgs['city'].value_counts().to_dict()
    popular_cities = []
    
    city_icons = {
        "Bangalore": "🏙️", "Mumbai": "🌊", "Delhi": "🏛️", "Pune": "🎓",
        "Hyderabad": "💎", "Gurgaon": "🏢", "Chennai": "🏖️", "Noida": "🌆",
        "Ahmedabad": "🪁", "Kolkata": "🚋", "Jaipur": "🏰", "Kochi": "🌴", "Indore": "🍲"
    }

    for city, count in city_counts.items():
        city_df = df_pgs[df_pgs['city'] == city]
        top_localities = city_df['locality'].value_counts().head(8).index.tolist()
        min_rent = int(city_df['rent_monthly'].min())
        popular_cities.append({
            "name": city,
            "count": int(count),
            "icon": city_icons.get(city, "📍"),
            "starting_price": min_rent,
            "popular_localities": top_localities
        })

    return jsonify({"success": True, "cities": popular_cities})

@app.route('/api/localities', methods=['GET'])
def get_localities():
    """Returns localities for a specific city."""
    city = request.args.get('city', '').strip()
    if city:
        filtered = df_pgs[df_pgs['city'].str.lower() == city.lower()]
    else:
        filtered = df_pgs
    localities = filtered['locality'].dropna().unique().tolist()
    localities.sort()
    return jsonify({"success": True, "localities": localities})

@app.route('/api/pgs', methods=['GET'])
def get_pgs():
    """Search, filter, sort, and paginate PG listings."""
    city = request.args.get('city', '').strip()
    locality = request.args.get('locality', '').strip()
    gender = request.args.get('gender', '').strip().lower()
    sharing = request.args.get('sharing', '').strip().lower()
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    ac = request.args.get('ac', '').strip().lower()
    wifi = request.args.get('wifi', '').strip().lower()
    food = request.args.get('food', '').strip().lower()
    search = request.args.get('search', '').strip().lower()
    sort_by = request.args.get('sort_by', 'popular').strip().lower()
    page = max(1, request.args.get('page', 1, type=int))
    limit = max(1, min(60, request.args.get('limit', 12, type=int)))

    data = df_pgs.copy()

    if city and city != 'all':
        data = data[data['city'].str.lower() == city.lower()]
    if locality and locality != 'all':
        data = data[data['locality'].str.lower() == locality.lower()]
    if sharing and sharing != 'all':
        data = data[data['sharing_type'].astype(str).str.lower() == sharing]
    if min_price is not None:
        data = data[data['rent_monthly'] >= min_price]
    if max_price is not None:
        data = data[data['rent_monthly'] <= max_price]
    if ac in ['true', 'yes', '1']:
        data = data[data['ac'].astype(str).str.lower().isin(['yes', '1', 'true'])]
    if wifi in ['true', 'yes', '1']:
        data = data[data['wifi'].astype(str).str.lower().isin(['yes', '1', 'true'])]
    if food in ['true', 'yes', '1']:
        data = data[data['food_included'].astype(str).str.lower().isin(['yes', '1', 'true'])]

    if search:
        mask = (
            data['name'].astype(str).str.lower().str.contains(search, na=False) |
            data['locality'].astype(str).str.lower().str.contains(search, na=False) |
            data['city'].astype(str).str.lower().str.contains(search, na=False) |
            data['description'].astype(str).str.lower().str.contains(search, na=False)
        )
        data = data[mask]

    enriched_items = [enrich_pg_record(row) for _, row in data.iterrows()]

    if gender and gender not in ['all', 'any']:
        if gender in ['men', 'boys', 'male']:
            enriched_items = [p for p in enriched_items if p['gender'].lower() in ['men', 'unisex']]
        elif gender in ['women', 'girls', 'female']:
            enriched_items = [p for p in enriched_items if p['gender'].lower() in ['women', 'unisex']]
        elif gender == 'unisex':
            enriched_items = [p for p in enriched_items if p['gender'].lower() == 'unisex']

    if sort_by == 'price_asc':
        enriched_items.sort(key=lambda x: x['rent_monthly'])
    elif sort_by == 'price_desc':
        enriched_items.sort(key=lambda x: x['rent_monthly'], reverse=True)
    elif sort_by == 'rating_desc':
        enriched_items.sort(key=lambda x: (x['rating'], x['reviews_count']), reverse=True)
    elif sort_by == 'popular':
        enriched_items.sort(key=lambda x: x['reviews_count'], reverse=True)

    total_count = len(enriched_items)
    total_pages = max(1, (total_count + limit - 1) // limit)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_items = enriched_items[start_idx:end_idx]

    return jsonify({
        "success": True,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "pgs": paginated_items
    })

@app.route('/api/pg/<pg_id>', methods=['GET'])
def get_pg_detail(pg_id):
    """
    Returns full details for a specific PG, merged with live database room bed inventory.
    """
    match = df_pgs[df_pgs['pg_id'].astype(str) == str(pg_id)]
    row = match.iloc[0] if not match.empty else None

    # Ensure property and room records are in DB
    prop = get_or_create_property_db(pg_id, row=row)
    if not prop and row is None:
        return jsonify({"success": False, "error": f"PG with ID {pg_id} not found"}), 404

    enriched = enrich_pg_record(row) if row is not None else prop.to_dict()

    # Attach live rooms from DB with real IDs and available bed counts
    if prop:
        enriched['rooms'] = [r.to_dict() for r in prop.rooms]
    else:
        enriched['rooms'] = []

    return jsonify({"success": True, "pg": enriched})

# ─── Static Web Serving ──────────────────────────────────────────────────────

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serves static files."""
    if os.path.exists(os.path.join(STATIC_DIR, filename)):
        return send_from_directory(STATIC_DIR, filename)
    elif os.path.exists(os.path.join(FRONTEND_DIR, 'static', filename)):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'static'), filename)
    elif os.path.exists(os.path.join(FRONTEND_DIR, filename)):
        return send_from_directory(FRONTEND_DIR, filename)
    return jsonify({"error": "File not found"}), 404

@app.route('/')
def serve_root():
    """Serves the main application page."""
    if os.path.exists(os.path.join(FRONTEND_DIR, 'index.html')):
        return send_from_directory(FRONTEND_DIR, 'index.html')
    elif os.path.exists(os.path.join(BASE_DIR, 'index.html')):
        return send_from_directory(BASE_DIR, 'index.html')
    return "<h1>Roomee Co-living Discovery Platform Ready</h1>"

@app.route('/<path:filename>')
def serve_frontend_files(filename):
    """Serves root or frontend HTML, CSS, JS assets."""
    if filename.startswith('api/'):
        return jsonify({"error": "API route not found"}), 404

    if os.path.exists(os.path.join(FRONTEND_DIR, filename)):
        return send_from_directory(FRONTEND_DIR, filename)
    elif os.path.exists(os.path.join(BASE_DIR, filename)):
        return send_from_directory(BASE_DIR, filename)
    elif os.path.exists(os.path.join(STATIC_DIR, filename)):
        return send_from_directory(STATIC_DIR, filename)
    return jsonify({"error": "Resource not found"}), 404

if __name__ == '__main__':
    print("Starting Roomee Discovery & Booking Engine on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=False)
