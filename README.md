# 🏠 PGFinder — AI-Powered Smart PG Recommendation System

PGFinder is a premium web application designed to help students in Gujarat find the perfect Paying Guest (PG) accommodation near their colleges in **Ahmedabad** and **Anand**. Using an intelligent mathematical scoring system and data-driven insights, it dynamically ranks accommodation options based on affordability, proximity, and essential amenities.

---

## ✨ Features

- **Premium Dark UI**: Implements a sleek, responsive Glassmorphism interface with custom animated background ambient orbs and smooth CSS transitions.
- **College-to-City Smart Inference**: Students simply select their college, and the backend automatically deduces whether they need accommodations in Ahmedabad or Anand.
- **Multi-Criteria Ranking Matrix**: Accommodations are not just filtered; they are evaluated using a custom weighted formulation:
  $$\text{PG Score} = (0.30 \times \text{Amenities}) + (0.30 \times \text{Proximity}) + (0.40 \times \text{Affordability})$$
- **Dynamic Rent Bounds**: Real-time slide adjustments with custom gradient filling and dynamic category ticks (Budget, Mid-range, Premium).
- **Visual AI Rank Badges**: Top results feature custom visual indicator badges (🥇 Gold, 🥈 Silver, 🥉 Bronze) alongside real-time metrics and breakdown scores.

---

## 📂 Project Structure

```text
├── app.py                         # Flask Web Server (Backend Filtering & Core Logic)
├── app.js                         # Frontend controller logic, API calls & DOM Renderer
├── index.html                     # Responsive entry point web layout
├── style.css                      # Premium Dark Glassmorphism Stylesheet
├── pg_dataset_final_v2_named.csv  # Cleaned dataset consisting of PG listings
└── pg.ipynb                       # Jupyter Notebook mapping exploratory data research
