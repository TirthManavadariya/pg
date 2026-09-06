import os
import sys
import time
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(__file__))

from models.rent_predictor import rent_predictor, clean_dataframe
from models.semantic_search import semantic_engine
from models.neural_matcher import neural_recommender

DATASET_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), '..', 'pg_listings.csv'),
    os.path.join(os.path.dirname(__file__), 'pg_listings.csv'),
    os.path.join(os.path.dirname(__file__), '..', 'pg_dataset_final_v2_named.csv')
]

def find_dataset():
    for p in DATASET_CANDIDATES:
        if os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError("Could not locate pg_listings.csv dataset.")

def run_training_pipeline():
    start_time = time.time()
    csv_path = find_dataset()
    print("=" * 60)
    print("ROOMEE AI/ML/DL TRAINING PIPELINE")
    print(f"Dataset: {csv_path}")
    print("=" * 60)

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df):,} listings with columns: {list(df.columns)}")

    # 1. Train Fair Rent Predictor
    print("\n[STEP 1/3] Training Fair Rent Predictor (Scikit-Learn/GradientBoosting)...")
    rent_predictor.train(df)

    # 2. Build Semantic Vector Index
    print("\n[STEP 2/3] Building AI Semantic Vector Search Index...")
    semantic_engine.build_index(df)

    # 3. Train PyTorch Two-Tower Neural Matcher
    print("\n[STEP 3/3] Training PyTorch Two-Tower Matching Network...")
    neural_recommender.train(df, epochs=10)

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"SUCCESS: ALL ROOMEE AI/ML MODELS TRAINED & PERSISTED in {elapsed:.2f}s!")
    print("=" * 60)

if __name__ == '__main__':
    run_training_pipeline()
