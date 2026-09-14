# 🏠 Roomee — Live Google Maps PG Discovery & AI Accommodation Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![Google Maps](https://img.shields.io/badge/Maps-Google%20Places%20(New)-4285F4.svg)](https://developers.google.com/maps)
[![PyTorch](https://img.shields.io/badge/Deep%20Learning-PyTorch-EE4C2C.svg)](https://pytorch.org/)
[![Scikit-Learn](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](#license)

**Roomee** is a production-grade, full-stack student and professional accommodation discovery engine. It pairs **live real-world Google Places API (New)** discovery and an interactive **split-screen Google Maps UI** with an **AI/ML housing recommendation pipeline**, role-based authentication, and visit/booking management across 7 premier Indian metropolitan hubs: **Ahmedabad, Gandhinagar, Mumbai, Pune, Bangalore, Hyderabad, and Delhi**.

---

## 🌟 Key Highlights & Modules

### 1. 🗺️ Real Google Maps PG Discovery (Split-Screen Overhaul)
- **Live Google Places API (New) Integration**: Retrieves authentic, real-world PG accommodation listings via `https://places.googleapis.com/v1/places:searchText` using 20 km radius circle biasing.
- **7 Target Cities Supported**:
  - **Ahmedabad**: `(23.0225, 72.5714)`
  - **Gandhinagar**: `(23.2156, 72.6369)`
  - **Mumbai**: `(19.0760, 72.8777)`
  - **Pune**: `(18.5204, 73.8567)`
  - **Bangalore**: `(12.9716, 77.5946)`
  - **Hyderabad**: `(17.3850, 78.4867)`
  - **Delhi**: `(28.6139, 77.2090)`
- **Full-Stack Split-Screen Layout**:
  - **Sticky City Selector**: Horizontal pill buttons for all 7 cities with smooth active indicator transitions and dynamic place counts.
  - **Left Feed Panel (44%)**: Vertical scroll feed displaying PG cards with numbered badges, verified indicators, ratings, review counts, pricing, complete addresses, and direct *"Open in Google Maps"* links.
  - **Local Real-Time Filter**: Instant substring matching by neighborhood, street name, or PG title with live count updates.
  - **Right Map Panel (56%)**: Full-height interactive map featuring custom numbered SVG pin markers. Hovering any card triggers pin bounce animations; clicking a pin opens a styled `InfoWindow` and automatically scrolls the corresponding card into view.
  - **Adaptive Dual-Engine Mapping**: Connects to the **Google Maps JavaScript API** when `GOOGLE_MAPS_API_KEY` is configured, and seamlessly falls back to a clean **OpenStreetMap vector engine** with zero watermarks if unconfigured.
  - **Mobile Responsive Viewport (`< 768px`)**: Automatically transitions into a floating bottom pill toggle (`[ 📋 List View ]  |  [ 🗺️ Map View ]`).

### 2. 🤖 AI & Machine Learning Pipeline
- **PyTorch Two-Tower Deep Neural Matcher**: 32-dimensional normalized latent space mapping user preferences against accommodation tensors.
- **Semantic Vector Search (NLP Embeddings)**: Converts natural language descriptions into dense vector embeddings for intent-driven search.
- **Fair Market Rent Valuation Predictor**: GradientBoosting/XGBoost regressor trained on 30,000+ listings predicting fair benchmarks and flagging *Great Value* deals.

### 3. 🛡️ Production Database & Booking Lifecycle
- **Persistent SQLite/PostgreSQL Database**: Models for `User`, `PGProperty`, `Room`, `Booking`, and `Payment` with ACID concurrency control.
- **Role-Based Access Control (RBAC)**: JWT authentication securing student, property owner, and admin endpoints.
- **Visit Scheduling & Booking Flow**: Instant visit slot confirmation and token booking payment workflows (Razorpay/Stripe compatible).

---

## 🏗️ System Architecture

```
                       ┌─────────────────────────────────────────┐
                       │   Client UI (Split-Screen & Grid Views) │
                       │    (discovery.html / index.html)        │
                       └────────────────────┬────────────────────┘
                                            │
                ┌───────────────────────────┴───────────────────────────┐
                ▼                                                       ▼
  ┌───────────────────────────┐                           ┌───────────────────────────┐
  │   Google Maps JS / Leaflet│                           │   Flask REST API Server   │
  │   Interactive Map Canvas  │                           │   (backend/app.py)        │
  └───────────────────────────┘                           └─────────────┬─────────────┘
                                                                        │
        ┌───────────────────────────────┬───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼                               ▼
┌───────────────┐               ┌───────────────┐               ┌───────────────┐               ┌───────────────┐
│ Google Places │               │ SQLite / DB   │               │ AI/ML Models  │               │ 30k Listings  │
│ API (New)     │               │ (roomee.db)   │               │ (Two-Tower &  │               │ Dataset       │
│ (real_places) │               │ Models & Auth │               │ Regressor)    │               │ (CSV Engine)  │
└───────────────┘               └───────────────┘               └───────────────┘               └───────────────┘
```

---

## 📁 Repository Structure

```text
pg/
├── backend/
│   ├── app.py                  # Production Flask API server & route handlers
│   ├── real_places.py          # Google Places API (New) client & verified city fallbacks
│   ├── models_db.py            # SQLAlchemy database models (User, Booking, Room, etc.)
│   ├── auth.py                 # JWT authentication & password verification
│   ├── notifications.py        # Event notification hooks & dispatcher
│   ├── chat_parser.py          # Conversational assistant parser
│   ├── train_models.py         # AI model training script
│   └── requirements.txt        # Backend dependencies
├── frontend/
│   ├── discovery.html          # Real Google Maps Split-Screen Discovery UI
│   ├── index.html              # Modern marketplace landing & grid view
│   ├── pgfinder.html           # Intelligent student housing ranking dashboard
│   ├── app.js                  # Frontend client application logic
│   └── style.css               # Design system & responsive styles
├── discovery.html              # Root discovery entrypoint
├── index.html                  # Root marketplace landing entrypoint
├── app.py                      # Root server entrypoint delegating to backend/app.py
├── pg_listings.csv             # 30,000+ PG listings dataset
├── .env                        # Environment configuration (Google Maps API key, etc.)
└── README.md                   # Platform documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (tested through Python 3.14)
- Web Browser (Chrome, Edge, Firefox, Safari)

### 2. Configuration (`.env`)
Create or edit `.env` in the root workspace directory:
```env
# Optional: Enter your Google Maps JavaScript & Places API (New) key:
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

PORT=5000
DATABASE_URL=sqlite:///instance/roomee.db
```
> **Note**: If `GOOGLE_MAPS_API_KEY` is left blank, Roomee seamlessly operates out-of-the-box using curated authentic real-world PG listings across all 7 cities with clean vector map tiles.

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Run the Server
```bash
python app.py
```

Open your browser and navigate to:
- **Real Google Maps Split-Screen Discovery**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/) (or `/discovery`)
- **Classic Marketplace Grid View**: [http://127.0.0.1:5000/classic](http://127.0.0.1:5000/classic)
- **Student Housing Discovery**: [http://127.0.0.1:5000/pgfinder.html](http://127.0.0.1:5000/pgfinder.html)

---

## 🔌 REST API Reference

### Real Google Places & Maps Discovery
| Endpoint | Method | Parameters | Description |
|---|---|---|---|
| `/api/real-pgs` | `GET` | `city` (e.g. `ahmedabad`, `bangalore`) | Returns live Google Places (New) PG listings with GPS coordinates, reviews, ratings, and Google Maps links. |
| `/api/config` | `GET` | — | Returns public SDK configuration and supported city coordinates. |

#### Sample Response (`GET /api/real-pgs?city=ahmedabad`):
```json
{
  "success": true,
  "city": "ahmedabad",
  "center": { "lat": 23.0225, "lng": 72.5714 },
  "count": 8,
  "data": [
    {
      "id": "ChIJ_zO4-QWEXjkR4UoO7E3YlC4",
      "name": "Stanza Living Stanford House (Navrangpura)",
      "address": "Opp. St. Xavier's College, Navrangpura, Ahmedabad, Gujarat 380009",
      "lat": 23.0373,
      "lng": 72.5567,
      "rating": 4.6,
      "reviews": 182,
      "mapsUrl": "https://maps.google.com/?q=Stanza+Living+Stanford+House+Navrangpura+Ahmedabad",
      "price": "₹9,500/mo",
      "gender": "Unisex"
    }
  ]
}
```

### Marketplace & Booking Endpoints
| Endpoint | Method | Description |
|---|---|---|
| `/api/cities` | `GET` | Returns list of major cities with starting rent and listing counts. |
| `/api/localities` | `GET` | Returns localities for a specific city (`?city=Bangalore`). |
| `/api/pgs` | `GET` | Search and filter listings by price, gender, sharing type, amenities. |
| `/api/pg/<pg_id>` | `GET` | Fetches detailed property specifications and available room inventory. |
| `/api/auth/register` | `POST` | User registration (Student / Owner / Admin). |
| `/api/auth/login` | `POST` | User login returning JWT bearer token. |
| `/api/auth/me` | `GET` | Fetches current user profile from token. |
| `/api/book-visit` | `POST` | Confirms free on-site property visits. |
| `/api/bookings` | `POST` | Reserves bed / room with concurrency check. |
| `/api/payments/create-order`| `POST` | Generates secure checkout order token (Razorpay/Stripe). |
| `/api/payments/verify` | `POST` | Confirms payment transaction and activates booking. |

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.
