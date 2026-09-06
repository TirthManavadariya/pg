"""
backend/app.py
High-Performance, Roomee PG Discovery Backend API.
Provides lightning-fast search, filtering, sorting, pagination, property details, and visit scheduling.
"""

import os
import sys
import hashlib
import random
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=None)
CORS(app)

# Load dataset
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
    img_set_idx = h % len(PROPERTY_IMAGE_SETS)
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
    # Single ~ 1.5x base, Double ~ 1.0x, Triple ~ 0.75x, Four/Dorm ~ 0.55x
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
            
    print(f"Successfully loaded {len(df_pgs)} listings.")

load_data()

# ─── API Routes ─────────────────────────────────────────────────────────────

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Returns top cities with total listings and top localities."""
    city_counts = df_pgs['city'].value_counts().to_dict()
    popular_cities = []
    
    city_icons = {
        "Bangalore": "🏙️",
        "Mumbai": "🌊",
        "Delhi": "🏛️",
        "Pune": "🎓",
        "Hyderabad": "💎",
        "Gurgaon": "🏢",
        "Chennai": "🏖️",
        "Noida": "🌆",
        "Ahmedabad": "🪁",
        "Kolkata": "🚋",
        "Jaipur": "🏰",
        "Kochi": "🌴",
        "Indore": "🍲"
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
    # Query parameters
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

    # City filter
    if city and city != 'all':
        data = data[data['city'].str.lower() == city.lower()]

    # Locality filter
    if locality and locality != 'all':
        data = data[data['locality'].str.lower() == locality.lower()]

    # Sharing filter
    if sharing and sharing != 'all':
        data = data[data['sharing_type'].astype(str).str.lower() == sharing]

    # Price filters
    if min_price is not None:
        data = data[data['rent_monthly'] >= min_price]
    if max_price is not None:
        data = data[data['rent_monthly'] <= max_price]

    # AC filter
    if ac == 'true' or ac == 'yes' or ac == '1':
        data = data[data['ac'].astype(str).str.lower().isin(['yes', '1', 'true'])]

    # WiFi filter
    if wifi == 'true' or wifi == 'yes' or wifi == '1':
        data = data[data['wifi'].astype(str).str.lower().isin(['yes', '1', 'true'])]

    # Food filter
    if food == 'true' or food == 'yes' or food == '1':
        data = data[data['food_included'].astype(str).str.lower().isin(['yes', '1', 'true'])]

    # Search keyword filter
    if search:
        mask = (
            data['name'].astype(str).str.lower().str.contains(search, na=False) |
            data['locality'].astype(str).str.lower().str.contains(search, na=False) |
            data['city'].astype(str).str.lower().str.contains(search, na=False) |
            data['description'].astype(str).str.lower().str.contains(search, na=False)
        )
        data = data[mask]

    # Enrich data rows
    enriched_items = [enrich_pg_record(row) for _, row in data.iterrows()]

    # Gender filter (applied after enrichment)
    if gender and gender not in ['all', 'any']:
        if gender in ['men', 'boys', 'male']:
            enriched_items = [p for p in enriched_items if p['gender'].lower() in ['men', 'unisex']]
        elif gender in ['women', 'girls', 'female']:
            enriched_items = [p for p in enriched_items if p['gender'].lower() in ['women', 'unisex']]
        elif gender == 'unisex':
            enriched_items = [p for p in enriched_items if p['gender'].lower() == 'unisex']

    # Sorting
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
    """Returns full details for a specific PG."""
    match = df_pgs[df_pgs['pg_id'].astype(str) == str(pg_id)]
    if match.empty:
        return jsonify({"success": False, "error": f"PG with ID {pg_id} not found"}), 404
        
    enriched = enrich_pg_record(match.iloc[0])
    return jsonify({"success": True, "pg": enriched})

@app.route('/api/book-visit', methods=['POST'])
def book_visit():
    """Handles schedule a visit bookings."""
    payload = request.get_json(force=True, silent=True) or {}
    pg_id = payload.get('pg_id', '').strip()
    name = payload.get('name', '').strip()
    phone = payload.get('phone', '').strip()
    date = payload.get('date', '').strip()
    slot = payload.get('slot', 'Morning (10 AM - 1 PM)').strip()

    if not name or not phone:
        return jsonify({"success": False, "error": "Name and Phone number are required"}), 400

    booking_id = f"ROOMEE-VISIT-{random.randint(100000, 999999)}"
    
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
    # Check frontend/index.html or root index.html
    if os.path.exists(os.path.join(FRONTEND_DIR, 'index.html')):
        return send_from_directory(FRONTEND_DIR, 'index.html')
    elif os.path.exists(os.path.join(BASE_DIR, 'index.html')):
        return send_from_directory(BASE_DIR, 'index.html')
    return "<h1>Roomee Co-living Discovery Platform Ready</h1>"

@app.route('/<path:filename>')
def serve_frontend_files(filename):
    """Serves root or frontend HTML, CSS, JS assets."""
    # Avoid intercepting API routes
    if filename.startswith('api/'):
        return jsonify({"error": "API route not found"}), 404

    # Look in frontend directory
    if os.path.exists(os.path.join(FRONTEND_DIR, filename)):
        return send_from_directory(FRONTEND_DIR, filename)
    # Look in base directory
    elif os.path.exists(os.path.join(BASE_DIR, filename)):
        return send_from_directory(BASE_DIR, filename)
    # Look in static
    elif os.path.exists(os.path.join(STATIC_DIR, filename)):
        return send_from_directory(STATIC_DIR, filename)
    return jsonify({"error": "Resource not found"}), 404

if __name__ == '__main__':
    print("Starting Roomee Discovery Engine on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=False)
