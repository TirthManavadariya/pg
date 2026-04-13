from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import numpy as np
import os

app = Flask(__name__, static_folder='static', template_folder='static')

# ─── Load & Preprocess Dataset ────────────────────────────────────────────────
df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'pg_dataset_final_v2_named.csv'))

for col in ['AC', 'WiFi', 'Food']:
    df[col] = df[col].map({'Yes': 1, 'No': 0})


df['amenities_score'] = df[['AC', 'WiFi', 'Food']].sum(axis=1)
df['distance_score']  = 1 / df['Distance_km']
df['affordability']   = 1 / df['Rent']

df['PG_Score'] = (
    0.30 * df['amenities_score'] +
    0.30 * df['distance_score']  +
    0.40 * df['affordability']
)

score_min = df['PG_Score'].min()
score_max = df['PG_Score'].max()
df['rank_score'] = ((df['PG_Score'] - score_min) / (score_max - score_min) * 100).round(2)


ANAND_AREA_MAP = {
    'Bopal':        'V.V. Nagar',
    'Vastrapur':    'Karamsad',
    'Navrangpura':  'Anand City Center',
    'Maninagar':    'Old Anand',
    'Satellite':    'Station Road',
}

# College → City mapping (user picks college, we infer city)
COLLEGE_CITY = {
    "Nirma University":          "Ahmedabad",
    "PDPU":                      "Ahmedabad",
    "Gujarat University":        "Ahmedabad",
    "CEPT University":           "Ahmedabad",
    "Ahmedabad University":      "Ahmedabad",
    "LDRP Institute":            "Ahmedabad",
    "ADIT College":              "Anand",
    "CVM University":            "Anand",
    "Anand Agricultural Uni":    "Anand",
    "SRICT Institute":           "Anand",
    "Anand Engineering College": "Anand",
}

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(force=True)
    gender     = data.get('gender', '').strip()       
    college    = data.get('college', '').strip()
    max_rent   = float(data.get('max_rent', 15000))

    # Resolve city from college
    city = COLLEGE_CITY.get(college, None)
    if city is None:
        return jsonify({"error": f"Unknown college: {college}"}), 400

    # Filter dataset
    mask = (df['Rent'] <= max_rent) & (df['City'] == city)

    if gender in ['Boys', 'Girls']:
        mask = mask & (df['Gender'].isin([gender, 'Unisex']))

    filtered = df[mask].copy()

    if filtered.empty:
        return jsonify({"pgs": [], "city": city, "message": "No PGs found matching your criteria."})

    f_min = filtered['PG_Score'].min()
    f_max = filtered['PG_Score'].max()
    if f_max > f_min:
        filtered['rank_score'] = ((filtered['PG_Score'] - f_min) / (f_max - f_min) * 100).round(2)
    else:
        filtered['rank_score'] = 100.0

    filtered = filtered.sort_values('rank_score', ascending=False)

    results = []
    for _, row in filtered.head(20).iterrows():
        # Fix misleading Ahmedabad area names in Anand city records
        area = row['Area']
        if row['City'] == 'Anand':
            area = ANAND_AREA_MAP.get(area, area)

        results.append({
            "name":          row['PG_Name'],
            "city":          row['City'],
            "area":          area,
            "rent":          int(row['Rent']),
            "distance_km":   round(row['Distance_km'], 2),
            "food":          "Yes" if row['Food'] == 1 else "No",
            "wifi":          "Yes" if row['WiFi'] == 1 else "No",
            "ac":            "Yes" if row['AC'] == 1 else "No",
            "gender":        row['Gender'],
            "transport":     row['Near_Transport'],
            "label":         row['Label'],
            "rank_score":    float(row['rank_score']),
            "amenities":     int(row['amenities_score']),
        })

    return jsonify({"pgs": results, "city": city, "college": college, "total": len(filtered)})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/colleges', methods=['GET'])
def colleges():
    return jsonify({"colleges": list(COLLEGE_CITY.keys())})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
