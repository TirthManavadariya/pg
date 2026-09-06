import os
import re
import json
import joblib
import numpy as np
import pandas as pd

INDEX_PATH = os.path.join(os.path.dirname(__file__), 'faiss_index.bin')
METADATA_PATH = os.path.join(os.path.dirname(__file__), 'search_metadata.json')
EMBEDDINGS_PATH = os.path.join(os.path.dirname(__file__), 'embeddings.npy')
ENCODER_PATH = os.path.join(os.path.dirname(__file__), 'text_encoder.joblib')

class SemanticSearchEngine:
    def __init__(self, index_file=INDEX_PATH, meta_file=METADATA_PATH, emb_file=EMBEDDINGS_PATH, enc_file=ENCODER_PATH):
        self.index_file = index_file
        self.meta_file = meta_file
        self.emb_file = emb_file
        self.enc_file = enc_file
        self.encoder = None
        self.faiss_index = None
        self.embeddings = None
        self.metadata = []
        self.is_sentence_transformer = False

    def _init_encoder(self):
        """Try loading sentence-transformers/all-MiniLM-L6-v2 with fast fallback."""
        if self.encoder is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
            print("Loading sentence-transformers/all-MiniLM-L6-v2...")
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.is_sentence_transformer = True
            print("SentenceTransformer loaded successfully.")
        except Exception as e:
            print(f"Notice: SentenceTransformer offline/not available ({e}). Using optimized TF-IDF Dense Neural Text Embedder.")
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
            from sklearn.pipeline import Pipeline
            self.encoder = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=10000, stop_words='english', ngram_range=(1, 2))),
                ('svd', TruncatedSVD(n_components=128, random_state=42))
            ])
            self.is_sentence_transformer = False

    def build_index(self, df: pd.DataFrame):
        """Embed descriptions and build local FAISS / cosine vector index."""
        self._init_encoder()
        descriptions = df['description'].fillna('').astype(str).tolist()

        print(f"Embedding {len(descriptions)} PG listings descriptions...")
        if self.is_sentence_transformer:
            embeddings = self.encoder.encode(descriptions, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
            embeddings = np.array(embeddings, dtype='float32')
        else:
            self.encoder.fit(descriptions)
            embeddings = self.encoder.transform(descriptions)
            # L2 normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            embeddings = (embeddings / norms).astype('float32')
            joblib.dump(self.encoder, self.enc_file)
            print(f"Encoder pipeline saved to {self.enc_file}")

        self.embeddings = embeddings
        dim = embeddings.shape[1]

        # Build FAISS index if faiss is installed, else save dense embeddings
        try:
            import faiss
            index = faiss.IndexFlatIP(dim)
            index.add(embeddings)
            faiss.write_index(index, self.index_file)
            self.faiss_index = index
            print(f"FAISS index built and saved to {self.index_file} (dim={dim})")
        except Exception as e:
            print(f"FAISS binary build note ({e}). Saving dense embeddings matrix.")
            np.save(self.emb_file, embeddings)

        # Store metadata mapping
        self.metadata = df[['pg_id', 'name', 'city', 'locality', 'rent_monthly', 'sharing_type', 'ac', 'wifi', 'food_included', 'food_type', 'description']].to_dict(orient='records')
        with open(self.meta_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False)
        print("Semantic search metadata saved.")

    def load(self):
        """Load index, encoder and metadata from disk."""
        if not os.path.exists(self.meta_file):
            return False

        with open(self.meta_file, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

        if os.path.exists(self.enc_file):
            try:
                self.encoder = joblib.load(self.enc_file)
                self.is_sentence_transformer = False
                print("Loaded text encoder pipeline from disk.")
            except Exception as e:
                print("Could not load text encoder pipeline:", e)
                self._init_encoder()
        else:
            self._init_encoder()

        # Try loading FAISS index
        if os.path.exists(self.index_file):
            try:
                import faiss
                self.faiss_index = faiss.read_index(self.index_file)
                print("FAISS index loaded successfully.")
                return True
            except Exception as e:
                print("FAISS load note:", e)

        # Fallback to loading numpy embeddings
        if os.path.exists(self.emb_file):
            self.embeddings = np.load(self.emb_file)
            print(f"Dense vector embeddings loaded ({self.embeddings.shape[0]} items).")
            return True

        return False

    def search(self, query: str, city=None, max_budget=None, sharing_type=None, ac=None, wifi=None, food_included=None, top_k=20) -> list:
        """
        Embed query, execute vector similarity search, apply categorical & numeric filters.
        """
        if not self.metadata or (self.embeddings is None and self.faiss_index is None):
            if not self.load():
                return []

        # Auto-extract budget and city filters from natural query if not explicitly passed
        extracted_budget = None
        query_lower = query.lower()

        budget_match = re.search(r'(?:under|below|less than|budget|max|within|<=|<)?\s*(?:rs\.?|inr|₹)?\s*(\d+)\s*(k|thousand)?', query_lower)
        if budget_match:
            val_str, unit = budget_match.groups()
            try:
                val = float(val_str)
                if unit in ['k', 'thousand'] or val < 100:
                    val = val * 1000
                if val >= 2000 and val <= 60000:
                    extracted_budget = val
            except Exception:
                pass

        if max_budget is None and extracted_budget is not None:
            max_budget = extracted_budget

        # Embed query
        if self.is_sentence_transformer and hasattr(self.encoder, 'encode'):
            q_emb = self.encoder.encode([query], normalize_embeddings=True).astype('float32')
        elif self.encoder is not None:
            q_emb = self.encoder.transform([query])
            norm = np.linalg.norm(q_emb)
            if norm > 0:
                q_emb = q_emb / norm
            q_emb = q_emb.astype('float32')
        else:
            return []

        # Retrieve scores
        if self.faiss_index is not None:
            D, I = self.faiss_index.search(q_emb, min(len(self.metadata), 200))
            scores = D[0]
            indices = I[0]
        elif self.embeddings is not None:
            sims = np.dot(self.embeddings, q_emb.T).flatten()
            top_indices = np.argsort(sims)[::-1][:200]
            indices = top_indices
            scores = sims[top_indices]
        else:
            return []

        results = []
        for idx, score in zip(indices, scores):
            if idx < 0 or idx >= len(self.metadata):
                continue
            item = self.metadata[idx]

            # Apply filters
            if city and str(item.get('city', '')).strip().lower() != str(city).strip().lower():
                continue
            if max_budget and float(item.get('rent_monthly', 0)) > float(max_budget):
                continue
            if sharing_type and str(item.get('sharing_type', '')).strip().lower() != str(sharing_type).strip().lower():
                continue
            if ac is not None and ac != '' and str(item.get('ac', '')).lower() != str(ac).lower():
                continue
            if wifi is not None and wifi != '' and str(item.get('wifi', '')).lower() != str(wifi).lower():
                continue
            if food_included is not None and food_included != '' and str(item.get('food_included', '')).lower() != str(food_included).lower():
                continue

            item_copy = dict(item)
            match_pct = max(0, min(100, int((score + 1.0) / 2.0 * 100) if score <= 1.0 else int(score)))
            item_copy['similarity_score'] = round(float(score), 4)
            item_copy['match_percentage'] = match_pct
            results.append(item_copy)

            if len(results) >= top_k:
                break

        return results

# Global singleton
semantic_engine = SemanticSearchEngine()
