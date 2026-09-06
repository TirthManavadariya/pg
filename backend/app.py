import os
import sys
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add backend dir to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from models.rent_predictor import rent_predictor, clean_dataframe
from models.semantic_search import semantic_engine
from models.neural_matcher import neural_recommender

# Locate frontend static directory
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

# Use static_folder=None to prevent Flask's built-in static handler from intercepting POST API routes
app = Flask(__name__, static_folder=None)
CORS(app)

# Dataset path
CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pg_listings.csv'))
if not os.path.exists(CSV_PATH):
    CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'pg_listings.csv'))

df_raw = None
df_clean = None

def init_system():
    global df_raw, df_clean
    print("Initializing Roomee AI backend systems...")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Dataset not found at {CSV_PATH}")

    df_raw = pd.read_csv(CSV_PATH)
    df_clean = clean_dataframe(df_raw)
    print(f"Loaded {len(df_clean)} PG listings from {CSV_PATH}")

    # Load / Train Rent Predictor
    if not rent_predictor.load():
        print("Training Rent Predictor on startup...")
        rent_predictor.train(df_clean)

    # Load / Build Semantic Search
    if not semantic_engine.load():
        print("Building Semantic Search Index on startup...")
        semantic_engine.build_index(df_clean)

    # Load / Train Neural Matcher
    if not neural_recommender.load(df_clean):
        print("Training PyTorch Two-Tower Neural Matcher on startup...")
        neural_recommender.train(df_clean)

    print("Roomee AI Core Ready!")

# Initialize on startup
try:
    init_system()
except Exception as e:
    print(f"Warning during startup initialization: {e}")

# ─── Health Endpoint ──────────────────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "service": "Roomee AI PG Recommendation Engine",
        "listings_count": len(df_clean) if df_clean is not None else 0,
        "models": {
            "rent_predictor": rent_predictor.pipeline is not None,
            "semantic_search": semantic_engine.metadata is not None and len(semantic_engine.metadata) > 0,
            "neural_matcher": neural_recommender.is_ready
        }
    })

# ─── Metadata Endpoint (for dropdowns and UI chips) ───────────────────────────
@app.route('/api/meta', methods=['GET'])
def get_metadata():
    if df_clean is None:
        return jsonify({"error": "Dataset not loaded"}), 500

    cities = sorted(df_clean['city'].dropna().unique().tolist())
    localities = sorted(df_clean['locality'].dropna().unique().tolist())
    sharing_types = sorted(df_clean['sharing_type'].dropna().unique().tolist())
    min_rent = int(df_clean['rent_monthly'].min())
    max_rent = int(df_clean['rent_monthly'].max())

    return jsonify({
        "cities": cities,
        "localities": localities,
        "sharing_types": sharing_types,
        "price_range": {
            "min": min_rent,
            "max": max_rent,
            "avg": int(df_clean['rent_monthly'].mean())
        }
    })

# ─── Step 1: Fair Rent Predictor Endpoint ─────────────────────────────────────
@app.route('/api/predict-rent', methods=['POST'])
def predict_rent_endpoint():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Missing JSON request body"}), 400

        result = rent_predictor.predict(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Step 2: AI Semantic Search Endpoint ──────────────────────────────────────
@app.route('/api/semantic-search', methods=['POST'])
def semantic_search_endpoint():
    try:
        data = request.get_json(force=True)
        query = data.get('query', '').strip()
        if not query:
            return jsonify({"error": "Query string is required"}), 400

        city = data.get('city')
        max_budget = data.get('max_budget')
        sharing_type = data.get('sharing_type')
        ac = data.get('ac')
        wifi = data.get('wifi')
        food_included = data.get('food_included')
        top_k = int(data.get('top_k', 24))

        raw_results = semantic_engine.search(
            query=query,
            city=city,
            max_budget=max_budget,
            sharing_type=sharing_type,
            ac=ac,
            wifi=wifi,
            food_included=food_included,
            top_k=top_k
        )

        # Enrich results with Fair Rent evaluation badge
        results = []
        for item in raw_results:
            try:
                rent_eval = rent_predictor.predict({
                    'city': item.get('city'),
                    'locality': item.get('locality'),
                    'sharing_type': item.get('sharing_type'),
                    'ac': item.get('ac'),
                    'wifi': item.get('wifi'),
                    'food_included': item.get('food_included'),
                    'food_type': item.get('food_type'),
                    'actual_rent': item.get('rent_monthly')
                })
                item['fair_rent'] = rent_eval
            except Exception:
                pass
            results.append(item)

        return jsonify({
            "query": query,
            "count": len(results),
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Step 3: DL Neural Matcher Endpoint ───────────────────────────────────────
@app.route('/api/recommend-personalized', methods=['POST'])
def recommend_personalized_endpoint():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "User preference data required"}), 400

        top_k = int(data.get('top_k', 20))
        raw_recommendations = neural_recommender.recommend(data, top_k=top_k)

        # Enrich with Fair Rent evaluation
        recommendations = []
        for item in raw_recommendations:
            try:
                rent_eval = rent_predictor.predict({
                    'city': item.get('city'),
                    'locality': item.get('locality'),
                    'sharing_type': item.get('sharing_type'),
                    'ac': item.get('ac'),
                    'wifi': item.get('wifi'),
                    'food_included': item.get('food_included'),
                    'food_type': item.get('food_type'),
                    'actual_rent': item.get('rent_monthly')
                })
                item['fair_rent'] = rent_eval
            except Exception:
                pass
            recommendations.append(item)

        return jsonify({
            "user_profile": data,
            "count": len(recommendations),
            "recommendations": recommendations
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── AI Conversational Chatbot Assistant Endpoint ─────────────────────────────
@app.route('/api/chat', methods=['POST'])
@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json(force=True) or {}
        message = data.get('message', '').strip()
        if not message:
            return jsonify({
                "reply": "Hello! I am **Roomee AI**. How can I help you find your ideal student or professional PG accommodation?",
                "pgs": []
            })

        msg_lower = message.lower()

        # Greetings
        if msg_lower in ['hi', 'hello', 'hey', 'start', 'help', 'hi there']:
            return jsonify({
                "reply": "👋 Hi there! I'm **Roomee AI**, your student housing assistant.\n\nTell me what you're looking for, for example:\n• *'Single AC room in Pune under 15k with veg food'*\n• *'Affordable PG in Bangalore Koramangala with WiFi'*\n• *'What is the fair market rent for double sharing in Mumbai?'*",
                "pgs": []
            })

        # Price Inquiry Check
        if any(k in msg_lower for k in ['fair rent', 'price check', 'how much', 'cost of', 'predict rent', 'market rate', 'market average']):
            city = 'Pune'
            for c in ['Pune', 'Bangalore', 'Mumbai', 'Hyderabad', 'Delhi', 'Ahmedabad', 'Chennai', 'Gurgaon', 'Noida', 'Jaipur', 'Kolkata']:
                if c.lower() in msg_lower:
                    city = c
                    break
            sharing = 'Double'
            for s in ['Single', 'Double', 'Triple', 'Dorm']:
                if s.lower() in msg_lower:
                    sharing = s
                    break

            ac = 1 if 'ac' in msg_lower else 0
            food = 1 if ('food' in msg_lower or 'meal' in msg_lower or 'mess' in msg_lower) else 0

            rent_info = rent_predictor.predict({
                'city': city,
                'sharing_type': sharing,
                'ac': ac,
                'wifi': 1,
                'food_included': food
            })
            return jsonify({
                "reply": f"📊 **ML Fair Rent Analysis**: The estimated fair market rent for a **{sharing} sharing room** in **{city}** (with {'AC, ' if ac else ''}{'meals included, ' if food else ''}Wi-Fi) is **₹{rent_info['predicted_rent']:,} / month**.",
                "fair_rent": rent_info,
                "pgs": []
            })

        # Execute semantic search
        raw_results = semantic_engine.search(query=message, top_k=4)
        enriched = []
        for item in raw_results:
            try:
                rent_eval = rent_predictor.predict({
                    'city': item.get('city'),
                    'locality': item.get('locality'),
                    'sharing_type': item.get('sharing_type'),
                    'ac': item.get('ac'),
                    'wifi': item.get('wifi'),
                    'food_included': item.get('food_included'),
                    'food_type': item.get('food_type'),
                    'actual_rent': item.get('rent_monthly')
                })
                item['fair_rent'] = rent_eval
            except Exception:
                pass
            enriched.append(item)

        if enriched:
            top_item = enriched[0]
            reply = f"🔍 I found **{len(enriched)} verified accommodations** matching your description!\n\nTop pick: **{top_item.get('name')}** in {top_item.get('locality')}, {top_item.get('city')} at **₹{top_item.get('rent_monthly'):,}/mo** ({top_item.get('match_percentage')}% Match, {top_item.get('fair_rent', {}).get('deal_category', 'Fair Deal')})."
        else:
            reply = "I searched our listings but couldn't find a matching room for that specific query. Try asking for a specific city or adjusting your budget!"

        return jsonify({
            "reply": reply,
            "pgs": enriched
        })
    except Exception as e:
        return jsonify({"reply": f"I ran into an issue processing your request: {str(e)}", "pgs": []}), 500

# ─── General Listings Search & Filter Endpoint ────────────────────────────────
@app.route('/api/listings', methods=['GET'])
def get_listings():
    if df_clean is None:
        return jsonify({"error": "Dataset not initialized"}), 500

    city = request.args.get('city')
    locality = request.args.get('locality')
    sharing = request.args.get('sharing')
    max_rent = request.args.get('max_rent', type=float)
    ac = request.args.get('ac')
    wifi = request.args.get('wifi')
    food = request.args.get('food')
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=18, type=int)

    filtered = df_clean.copy()

    if city:
        filtered = filtered[filtered['city'].str.lower() == city.strip().lower()]
    if locality:
        filtered = filtered[filtered['locality'].str.lower() == locality.strip().lower()]
    if sharing:
        filtered = filtered[filtered['sharing_type'].str.lower() == sharing.strip().lower()]
    if max_rent:
        filtered = filtered[filtered['rent_monthly'] <= max_rent]
    if ac is not None and ac != '':
        ac_val = 1 if ac.lower() in ['1', 'true', 'yes'] else 0
        filtered = filtered[filtered['ac'] == ac_val]
    if wifi is not None and wifi != '':
        wifi_val = 1 if wifi.lower() in ['1', 'true', 'yes'] else 0
        filtered = filtered[filtered['wifi'] == wifi_val]
    if food is not None and food != '':
        food_val = 1 if food.lower() in ['1', 'true', 'yes'] else 0
        filtered = filtered[filtered['food_included'] == food_val]

    total_count = len(filtered)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit

    paged = filtered.iloc[start_idx:end_idx].to_dict(orient='records')

    # Add fair rent badge to each item
    for item in paged:
        try:
            item['fair_rent'] = rent_predictor.predict({
                'city': item.get('city'),
                'locality': item.get('locality'),
                'sharing_type': item.get('sharing_type'),
                'ac': item.get('ac'),
                'wifi': item.get('wifi'),
                'food_included': item.get('food_included'),
                'food_type': item.get('food_type'),
                'actual_rent': item.get('rent_monthly')
            })
        except Exception:
            pass

    return jsonify({
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": int(np.ceil(total_count / max(1, limit))),
        "listings": paged
    })

# ─── Static Frontend Serving (Explicit GET only) ──────────────────────────────
@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Roomee Flask Server on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
