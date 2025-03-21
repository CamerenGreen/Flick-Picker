import torch
import torch.nn as nn
import torch.optim as optim

class MatrixFactorizationModel(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim=50):
        super(MatrixFactorizationModel, self).__init__()
        self.user_embeddings = nn.Embedding(num_users, embedding_dim)
        self.item_embeddings = nn.Embedding(num_items, embedding_dim)
        self.user_biases = nn.Embedding(num_users, 1)
        self.item_biases = nn.Embedding(num_items, 1)

    def forward(self, user_ids, item_ids):
        user_embedding = self.user_embeddings(user_ids)
        item_embedding = self.item_embeddings(item_ids)
        user_bias = self.user_biases(user_ids).squeeze()
        item_bias = self.item_biases(item_ids).squeeze()
        dot_product = (user_embedding * item_embedding).sum(dim=1)
        return dot_product + user_bias + item_bias

    def train(self, users, items, ratings, epochs=10, lr=0.01):
        user_ids = torch.tensor([u.id for u in users], dtype=torch.long)
        item_ids = torch.tensor([i.id for i in items], dtype=torch.long)
        ratings = torch.tensor(ratings, dtype=torch.float32)

        optimizer = optim.Adam(self.parameters(), lr=lr)
        criterion = nn.MSELoss()

        for epoch in range(epochs):
            optimizer.zero_grad()
            predictions = self(user_ids, item_ids)
            loss = criterion(predictions, ratings)
            loss.backward()
            optimizer.step()
            print(f"Epoch {epoch+1}, Loss: {loss.item()}")

    def predict(self, user_id, item_ids):
        user_id = torch.tensor([user_id], dtype=torch.long)
        item_ids = torch.tensor(item_ids, dtype=torch.long)
        with torch.no_grad():
            predictions = self(user_id, item_ids)
        return predictions.numpy()