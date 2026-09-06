import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np

WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), 'neural_matcher.pt')
ITEM_EMBEDDINGS_PATH = os.path.join(os.path.dirname(__file__), 'item_embeddings.pt')

# Vocabulary definitions for deterministic tensor mapping
CITIES = ['Ahmedabad', 'Bangalore', 'Chennai', 'Delhi', 'Gurgaon', 'Hyderabad', 'Jaipur', 'Kolkata', 'Mumbai', 'Noida', 'Pune']
SHARING_TYPES = ['Single', 'Double', 'Triple', 'Four', 'Dorm']
FOOD_TYPES = ['Veg', 'Non-Veg', 'Both', 'None']

def get_one_hot(value: str, vocab: list) -> list:
    """Helper to produce one-hot list."""
    val_clean = str(value).strip().title()
    vec = [0.0] * len(vocab)
    if val_clean in vocab:
        vec[vocab.index(val_clean)] = 1.0
    return vec

class UserTower(nn.Module):
    """Encodes user requirements (city, budget, sharing, food, ac, wifi) into 32-dim vector."""
    def __init__(self, input_dim=len(CITIES) + len(SHARING_TYPES) + len(FOOD_TYPES) + 4, embed_dim=32):
        super(UserTower, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(64, 48),
            nn.ReLU(),
            nn.Linear(48, embed_dim)
        )

    def forward(self, x):
        emb = self.net(x)
        return F.normalize(emb, p=2, dim=-1)

class ItemTower(nn.Module):
    """Encodes PG Listing features (city, rent, sharing, food, ac, wifi) into 32-dim vector."""
    def __init__(self, input_dim=len(CITIES) + len(SHARING_TYPES) + len(FOOD_TYPES) + 4, embed_dim=32):
        super(ItemTower, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(64, 48),
            nn.ReLU(),
            nn.Linear(48, embed_dim)
        )

    def forward(self, x):
        emb = self.net(x)
        return F.normalize(emb, p=2, dim=-1)

class TwoTowerMatcher(nn.Module):
    def __init__(self, embed_dim=32):
        super(TwoTowerMatcher, self).__init__()
        self.user_tower = UserTower(embed_dim=embed_dim)
        self.item_tower = ItemTower(embed_dim=embed_dim)

    def forward(self, user_features, item_features):
        user_emb = self.user_tower(user_features)
        item_emb = self.item_tower(item_features)
        # Cosine similarity between normalized vectors is dot product
        similarity = torch.sum(user_emb * item_emb, dim=-1)
        return similarity, user_emb, item_emb

class NeuralRecommender:
    def __init__(self, weights_file=WEIGHTS_PATH, item_emb_file=ITEM_EMBEDDINGS_PATH):
        self.weights_file = weights_file
        self.item_emb_file = item_emb_file
        self.model = TwoTowerMatcher()
        self.item_embeddings = None
        self.items_df = None
        self.is_ready = False

    def _feature_vector(self, city: str, sharing: str, food: str, budget_or_rent: float, ac: int, wifi: int, food_inc: int) -> list:
        """Construct deterministic feature vector."""
        city_vec = get_one_hot(city, CITIES)
        sharing_vec = get_one_hot(sharing, SHARING_TYPES)
        food_vec = get_one_hot(food, FOOD_TYPES)

        # Normalize budget / rent to roughly [0, 1] range (assuming 3000 to 30000 range)
        norm_price = max(0.0, min(1.0, (float(budget_or_rent) - 3000.0) / 27000.0))

        ac_val = 1.0 if str(ac).lower() in ['1', 'true', 'yes'] else 0.0
        wifi_val = 1.0 if str(wifi).lower() in ['1', 'true', 'yes'] else 0.0
        food_inc_val = 1.0 if str(food_inc).lower() in ['1', 'true', 'yes'] else 0.0

        return city_vec + sharing_vec + food_vec + [norm_price, ac_val, wifi_val, food_inc_val]

    def build_item_features(self, df: pd.DataFrame):
        """Convert dataframe rows to item tensor matrix."""
        feature_list = []
        for _, row in df.iterrows():
            f = self._feature_vector(
                city=row.get('city', ''),
                sharing=row.get('sharing_type', ''),
                food=row.get('food_type', 'None'),
                budget_or_rent=row.get('rent_monthly', 10000),
                ac=row.get('ac', 0),
                wifi=row.get('wifi', 1),
                food_inc=row.get('food_included', 0)
            )
            feature_list.append(f)
        return torch.tensor(feature_list, dtype=torch.float32)

    def train(self, df: pd.DataFrame, epochs=12):
        """Train Two-Tower matching network with Triplet / Margin ranking loss."""
        print("Training PyTorch Two-Tower Neural Matcher...")
        self.model.train()
        self.items_df = df.copy()

        item_tensor = self.build_item_features(df)
        num_items = len(df)

        optimizer = torch.optim.AdamW(self.model.parameters(), lr=0.003, weight_decay=1e-4)

        # Synthetic matching batch training
        batch_size = 128
        for epoch in range(epochs):
            perm = torch.randperm(num_items)
            total_loss = 0.0
            batches = 0

            for i in range(0, num_items, batch_size):
                idx = perm[i:i + batch_size]
                if len(idx) < 4:
                    continue

                pos_items = item_tensor[idx]
                # Positive users with slight perturbation
                user_inputs = pos_items + torch.randn_like(pos_items) * 0.05

                # Negative items (shuffled)
                neg_idx = torch.roll(idx, shifts=1)
                neg_items = item_tensor[neg_idx]

                optimizer.zero_grad()

                user_emb = self.model.user_tower(user_inputs)
                pos_emb = self.model.item_tower(pos_items)
                neg_emb = self.model.item_tower(neg_items)

                pos_sim = torch.sum(user_emb * pos_emb, dim=-1)
                neg_sim = torch.sum(user_emb * neg_emb, dim=-1)

                # Margin Ranking Loss
                target = torch.ones_like(pos_sim)
                loss = F.margin_ranking_loss(pos_sim, neg_sim, target, margin=0.3)

                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                batches += 1

            if (epoch + 1) % 3 == 0 or epoch == epochs - 1:
                avg_loss = total_loss / max(1, batches)
                print(f"Two-Tower Neural Matcher - Epoch {epoch+1}/{epochs} | Loss: {avg_loss:.4f}")

        # Precompute and save item embeddings
        self.model.eval()
        with torch.no_grad():
            self.item_embeddings = self.model.item_tower(item_tensor)

        torch.save(self.model.state_dict(), self.weights_file)
        torch.save(self.item_embeddings, self.item_emb_file)
        print(f"Two-Tower model saved to {self.weights_file}")
        self.is_ready = True

    def load(self, df: pd.DataFrame):
        """Load pretrained model and item embeddings."""
        self.items_df = df.copy()
        if os.path.exists(self.weights_file) and os.path.exists(self.item_emb_file):
            try:
                self.model.load_state_dict(torch.load(self.weights_file, weights_only=True))
                self.item_embeddings = torch.load(self.item_emb_file, weights_only=True)
                self.model.eval()
                self.is_ready = True
                print("PyTorch Two-Tower Recommender weights & embeddings loaded.")
                return True
            except Exception as e:
                print("Error loading Neural Matcher weights:", e)

        # If files do not exist or failed to load, train on the fly
        print("Pretrained weights not found. Training Neural Matcher on listings...")
        self.train(df)
        return True

    def recommend(self, user_profile: dict, top_k=20) -> list:
        """
        Generate top personalized recommendations for user profile.
        user_profile format:
        {
            'city': 'Pune',
            'budget': 12000,
            'sharing_type': 'Single',
            'food_type': 'Veg',
            'ac': 1,
            'wifi': 1,
            'food_included': 1
        }
        """
        if not self.is_ready:
            raise RuntimeError("Neural Matcher is not ready.")

        user_vec = self._feature_vector(
            city=user_profile.get('city', ''),
            sharing=user_profile.get('sharing_type', ''),
            food=user_profile.get('food_type', 'None'),
            budget_or_rent=user_profile.get('budget', 12000),
            ac=user_profile.get('ac', 0),
            wifi=user_profile.get('wifi', 1),
            food_inc=user_profile.get('food_included', 0)
        )

        user_tensor = torch.tensor([user_vec], dtype=torch.float32)

        self.model.eval()
        with torch.no_grad():
            user_emb = self.model.user_tower(user_tensor)  # shape (1, 32)
            # Dot product with precomputed item embeddings (N, 32)
            sims = torch.mm(user_emb, self.item_embeddings.T).squeeze(0).cpu().numpy()

        # Score ranking
        top_indices = np.argsort(sims)[::-1]

        target_city = user_profile.get('city')
        max_budget = float(user_profile.get('budget', 100000))

        results = []
        for idx in top_indices:
            row = self.items_df.iloc[idx].to_dict()
            score = float(sims[idx])

            # Apply hard filtering if city is specified
            if target_city and str(row.get('city', '')).strip().lower() != str(target_city).strip().lower():
                continue

            # Budget tolerance (+15% acceptable for neural ranking)
            if float(row.get('rent_monthly', 0)) > max_budget * 1.25:
                continue

            # Scale match score to percentage 60% - 99%
            match_pct = max(50, min(99, int((score + 1.0) / 2.0 * 100)))
            row['neural_match_score'] = round(score, 4)
            row['match_percentage'] = match_pct
            results.append(row)

            if len(results) >= top_k:
                break

        return results

# Global singleton
neural_recommender = NeuralRecommender()
