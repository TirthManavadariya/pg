import os
import sys
import joblib
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model_rent.joblib')

CATEGORICAL_FEATURES = ['city', 'locality', 'sharing_type', 'food_type']
NUMERICAL_FEATURES = ['ac', 'wifi', 'food_included']

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess and clean raw listings dataframe."""
    df_clean = df.copy()

    # Binary transformations
    for col in ['ac', 'wifi', 'food_included']:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip().str.lower().map({
                'yes': 1, 'no': 0,
                '1': 1, '0': 0,
                'true': 1, 'false': 0
            }).fillna(0).astype(int)

    # Clean food_type
    if 'food_type' in df_clean.columns:
        df_clean['food_type'] = df_clean['food_type'].fillna('None').astype(str).str.strip()

    # Categorical string formatting
    for col in ['city', 'locality', 'sharing_type']:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('Unknown').astype(str).str.strip()

    return df_clean

class RentPredictor:
    def __init__(self, model_file=MODEL_PATH):
        self.model_file = model_file
        self.pipeline = None
        self.feature_names = []
        self.top_features = []

    def train(self, df: pd.DataFrame):
        """Train the Fair Rent ML Regressor pipeline on listings data."""
        df_clean = clean_dataframe(df)

        X = df_clean[CATEGORICAL_FEATURES + NUMERICAL_FEATURES]
        y = df_clean['rent_monthly']

        preprocessor = ColumnTransformer(
            transformers=[
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES),
                ('num', 'passthrough', NUMERICAL_FEATURES)
            ]
        )

        # GradientBoostingRegressor for high accuracy and robust generalization
        model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )

        self.pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', model)
        ])

        print(f"Training Fair Rent Regressor on {len(df_clean)} listings...")
        self.pipeline.fit(X, y)

        # Extract feature importances
        try:
            ohe = self.pipeline.named_steps['preprocessor'].named_transformers_['cat']
            cat_features = list(ohe.get_feature_names_out(CATEGORICAL_FEATURES))
            all_features = cat_features + NUMERICAL_FEATURES
            importances = self.pipeline.named_steps['regressor'].feature_importances_
            feature_imp = sorted(zip(all_features, importances), key=lambda x: x[1], reverse=True)
            self.top_features = feature_imp[:10]
        except Exception as e:
            print("Feature importance extraction notice:", e)

        # Save model
        joblib.dump(self.pipeline, self.model_file)
        print(f"Fair Rent model saved to {self.model_file}")
        self.log_top_features()

    def log_top_features(self):
        """Log top 10 most influential features for rent pricing."""
        print("=" * 50)
        print("TOP 10 FEATURE IMPORTANCES (Fair Rent Model):")
        print("=" * 50)
        if self.top_features:
            for rank, (feat, imp) in enumerate(self.top_features, 1):
                print(f"{rank:2d}. {feat:<35} : {imp * 100:6.2f}%")
        elif self.pipeline is not None:
            try:
                ohe = self.pipeline.named_steps['preprocessor'].named_transformers_['cat']
                cat_features = list(ohe.get_feature_names_out(CATEGORICAL_FEATURES))
                all_features = cat_features + NUMERICAL_FEATURES
                importances = self.pipeline.named_steps['regressor'].feature_importances_
                feature_imp = sorted(zip(all_features, importances), key=lambda x: x[1], reverse=True)
                for rank, (feat, imp) in enumerate(feature_imp[:10], 1):
                    print(f"{rank:2d}. {feat:<35} : {imp * 100:6.2f}%")
            except Exception as e:
                print("Could not compute feature importances:", e)
        print("=" * 50)

    def load(self):
        """Load trained pipeline if exists."""
        if os.path.exists(self.model_file):
            self.pipeline = joblib.load(self.model_file)
            return True
        return False

    def predict(self, input_data: dict) -> dict:
        """
        Predict fair rent and assess pricing value.
        """
        if self.pipeline is None:
            if not self.load():
                raise RuntimeError("Model pipeline not loaded. Train or save the model first.")

        # Normalize single record into DataFrame
        record = {
            'city': str(input_data.get('city', 'Unknown')).strip(),
            'locality': str(input_data.get('locality', 'Unknown')).strip(),
            'sharing_type': str(input_data.get('sharing_type', 'Double')).strip(),
            'food_type': str(input_data.get('food_type', 'None')).strip(),
            'ac': 1 if str(input_data.get('ac', 0)).lower() in ['1', 'true', 'yes'] else 0,
            'wifi': 1 if str(input_data.get('wifi', 1)).lower() in ['1', 'true', 'yes'] else 0,
            'food_included': 1 if str(input_data.get('food_included', 0)).lower() in ['1', 'true', 'yes'] else 0
        }

        df_input = pd.DataFrame([record])
        predicted_rent = float(self.pipeline.predict(df_input)[0])
        predicted_rent_rounded = round(predicted_rent, -1)

        actual_rent = input_data.get('actual_rent') or input_data.get('rent_monthly')
        if actual_rent is not None:
            try:
                actual_rent = float(actual_rent)
                diff = actual_rent - predicted_rent_rounded
                diff_pct = (diff / predicted_rent_rounded) * 100

                if diff_pct <= -10:
                    deal_category = "Great Value"
                    deal_badge_color = "emerald"
                    deal_explanation = f"₹{abs(int(diff)):,} below market average ({abs(diff_pct):.1f}% savings)"
                elif diff_pct >= 10:
                    deal_category = "Overpriced"
                    deal_badge_color = "amber"
                    deal_explanation = f"₹{int(diff):,} above estimated market rent (+{diff_pct:.1f}%)"
                else:
                    deal_category = "Fair Deal"
                    deal_badge_color = "indigo"
                    deal_explanation = "Competitively priced within market norm (±10%)"
            except (ValueError, TypeError):
                actual_rent = None
                deal_category = "Market Standard"
                deal_badge_color = "slate"
                deal_explanation = "Estimated benchmark"
                diff_pct = 0.0
        else:
            deal_category = "Estimated Fair Rent"
            deal_badge_color = "indigo"
            deal_explanation = "AI Calculated Fair Market Benchmark"
            diff_pct = 0.0

        return {
            "predicted_rent": int(predicted_rent_rounded),
            "actual_rent": int(actual_rent) if actual_rent is not None else None,
            "deal_category": deal_category,
            "deal_badge_color": deal_badge_color,
            "deal_difference_pct": round(diff_pct, 1),
            "deal_explanation": deal_explanation
        }

# Global singleton
rent_predictor = RentPredictor()
