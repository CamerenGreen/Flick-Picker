# model_bridge.py
import torch
from backend.models.MatrixFactorizationModel import MatrixFactorizationModel
from backend.models.ContentBasedModel import ContentBasedModel

mf_model = MatrixFactorizationModel(num_users=1000, num_items=1000)
cb_model = ContentBasedModel()

def train_mf_model(users, items, ratings):
    mf_model.train(users, items, ratings)

def predict_mf_model(user_id, item_ids):
    return mf_model.predict(user_id, item_ids)

def train_cb_model(items):
    cb_model.train(items)

def predict_cb_model(user_history, item_ids, topN=10):
    return cb_model.predict(user_history, item_ids, topN)