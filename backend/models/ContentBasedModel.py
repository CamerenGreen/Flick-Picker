from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ContentBasedModel:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.item_features = None

    def train(self, items):
        item_descriptions = [" ".join(item.genres) for item in items]
        self.item_features = self.vectorizer.fit_transform(item_descriptions)

    def predict(self, user_history, item_ids, topN=10):
        user_history_features = self.vectorizer.transform([" ".join(user_history)])
        similarities = cosine_similarity(user_history_features, self.item_features)
        similar_items = np.argsort(similarities[0])[::-1][:topN]
        return similar_items