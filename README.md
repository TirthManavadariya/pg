# 🏠 Roomee — AI-Powered PG & Student Housing Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![PyTorch](https://img.shields.io/badge/Deep%20Learning-PyTorch-EE4C2C.svg)](https://pytorch.org/)
[![Scikit-Learn](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](#license)

**Roomee** is a full-stack, AI-first student and professional accommodation recommendation platform. It combines **Machine Learning regression**, **Natural Language Semantic Vector Search**, and a **PyTorch Two-Tower Deep Neural Matching Network** to help students and working professionals find verified Paying Guest (PG) stays tailored to their preferences, budget, and location.

---

## ✨ Key Features

### 1. 🔍 AI Semantic Vector Search (NLP Embeddings)
- Search naturally using everyday language (e.g., *"Quiet single AC room in Pune under 15k with veg food"* or *"Spacious double sharing in Koramangala Bangalore near IT companies"*).
- Converts descriptions and queries into dense vector embeddings using a trained neural text encoder.
- Cosine similarity matching and post-filtering by city, budget, sharing type, and food inclusion.

### 2. 🤖 PyTorch Two-Tower Neural Matcher (Personalized Recommendations)
- Implements a **Two-Tower Neural Network** architecture in PyTorch:
  - **User Tower**: Deep MLP mapping student preferences (city, budget tensor, sharing type, dietary choices, amenities) into a 32-dimensional normalized latent space.
  - **Item Tower**: Deep MLP mapping accommodation attributes into the same 32-dimensional latent space.
- Calculates dot-product cosine similarity against precomputed listing tensors to deliver real-time personalized recommendations.

### 3. 📊 ML Fair Market Rent Predictor
- Preprocessing pipeline with binary feature transformers and One-Hot Encoders for cities, localities, and room types.
- GradientBoosting / XGBoost regressor trained on **30,000+ PG listings**.
- Every PG card displays a live **Fair-Price Valuation Badge**:
  - 🟢 **Great Value**: Asking rent is significantly below market benchmark (e.g. ₹2,000+ savings).
  - 🔵 **Fair Deal**: Market standard pricing (within ±10% norm).
  - 🟠 **Overpriced / Slightly High**: Premium pricing above estimated benchmark.

### 4. 💬 Conversational AI Housing Chatbot
- Built-in floating AI assistant (`Ask Roomee AI`) for interactive Q&A, fair rent inquiries, and instant PG discovery directly in a chat window.

### 5. 🎨 Modern Minimalist Frontend Design
- Clean, crisp **Airbnb / Notion / Stripe** white aesthetic (`#f8fafc` background, `#ffffff` cards, slate `#0f172a` typography, refined indigo `#4f46e5` accents).
- Interactive filter chips, segmented sharing controls, real-time budget range slider, and interactive accommodation detail modals.

---

## 🏗️ System Architecture

```
                                  ┌────────────────────────┐
                                  │   User Search/Query    │
                                  └───────────┬────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
          ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
          │  Semantic Search  │     │   Neural Matcher  │     │   Rent Predictor  │
          │  (Dense Vectors)  │     │ (PyTorch Two-Tower│     │ (GradientBoosting)│
          └─────────┬─────────┘     └─────────┬─────────┘     └─────────┬─────────┘
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │ Ranked & Enriched PGs   │
                                 │ (Fair Price + Match %)  │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │   Roomee Minimalist UI  │
                                 │  (Web & Chat Interface) │
                                 └─────────────────────────┘
```

---

## 📁 Repository Structure

```
pg/
├── backend/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── rent_predictor.py     # Step 1: Fair Rent Regressor Pipeline
│   │   ├── semantic_search.py    # Step 2: Semantic Vector Search Engine
│   │   ├── neural_matcher.py     # Step 3: PyTorch Two-Tower Neural Network
│   │   ├── model_rent.joblib     # Saved Fair Rent model pipeline
│   │   ├── text_encoder.joblib   # Saved text embedding vectorizer
│   │   ├── embeddings.npy        # Precomputed listing embeddings (30k rows)
│   │   ├── neural_matcher.pt     # PyTorch model weights
│   │   ├── item_embeddings.pt    # Precomputed 32-dim item latent tensors
│   │   └── search_metadata.json  # Listings metadata cache
│   ├── app.py                    # Flask API server & static asset handler
│   ├── train_models.py           # Training & persistence pipeline script
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── index.html                # Modern semantic HTML5 markup
│   ├── style.css                 # Airbnb/Notion minimalist design system
│   └── app.js                    # Client application & API controller
├── pg_listings.csv               # Dataset containing 30,000 PG accommodations
└── README.md                     # Project documentation
```

---

## 📊 Dataset Schema (`pg_listings.csv`)

The dataset contains 30,000 records across 11 major Indian metropolitan cities (*Pune, Bangalore, Mumbai, Hyderabad, Delhi, Ahmedabad, Chennai, Gurgaon, Noida, Jaipur, Kolkata*):

| Column | Type | Description |
|---|---|---|
| `pg_id` | String | Unique listing identifier (e.g. `PG000001`) |
| `name` | String | PG Accommodation name |
| `city` | String | Metro city location |
| `locality` | String | Neighborhood / area |
| `rent_monthly` | Integer | Monthly rent in INR (₹) |
| `sharing_type` | String | `Single`, `Double`, `Triple`, `Dorm` |
| `ac` | String / Binary | Air Conditioning (`Yes` / `No`) |
| `wifi` | String / Binary | High-Speed Wi-Fi (`Yes` / `No`) |
| `food_included`| String / Binary | Daily meals included (`Yes` / `No`) |
| `food_type` | String | `Veg`, `Non-Veg`, `Both`, `None` |
| `description` | String | Full text description for semantic embedding |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Git (optional)

### 2. Clone / Open Repository
```bash
cd d:/ACADMIC/CODING/PROJECT/pg
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. (Optional) Re-Train AI Models
To retrain the Fair Rent Regressor, rebuild the NLP vector index, and train the PyTorch Two-Tower Matcher from scratch:
```bash
python backend/train_models.py
```

### 5. Launch the Web Application
```bash
python backend/app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔌 API Documentation

| Endpoint | Method | Description | Sample Payload |
|---|---|---|---|
| `/api/health` | `GET` | Health check & model status | — |
| `/api/meta` | `GET` | Available cities, localities, sharing types | — |
| `/api/listings` | `GET` | Filtered & paginated accommodations | Query params: `city`, `sharing`, `max_rent`, `ac`, `wifi`, `food` |
| `/api/semantic-search` | `POST` | Natural language vector search | `{"query": "Single AC room in Pune under 15k", "top_k": 20}` |
| `/api/recommend-personalized` | `POST` | PyTorch Two-Tower student recommendations | `{"city": "Pune", "budget": 14000, "sharing_type": "Single", "food_type": "Veg", "ac": 1, "wifi": 1, "food_included": 1}` |
| `/api/predict-rent` | `POST` | ML Fair market price benchmark | `{"city": "Pune", "locality": "Baner", "sharing_type": "Double", "ac": 1, "wifi": 1, "food_included": 1}` |
| `/api/chat` | `POST` | Conversational housing assistant | `{"message": "Show me girls PGs in Mumbai with food"}` |

---

## 📈 Model Performance & Feature Importances

Top 10 features influencing monthly rent pricing:

```
 1. Room Sharing (Single Room)          : 46.05%
 2. Air Conditioning (AC)               : 14.97%
 3. Room Sharing (Double Sharing)       :  9.34%
 4. City (Mumbai Tier-1 Premium)        :  5.04%
 5. Food / Meal Plan Included           :  4.78%
 6. City (Bangalore Tech Hub)           :  3.45%
 7. City (Gurgaon Cyber City)           :  2.64%
 8. City (Ahmedabad)                    :  2.49%
 9. City (Kolkata)                      :  2.24%
10. Room Sharing (Dormitory)            :  2.13%
```

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.
