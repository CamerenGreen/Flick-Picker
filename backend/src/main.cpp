#include "HybridRecommender.h"
#include <iostream>

int main() {
    // Example usage
    HybridRecommender recommender("bba50e797d1bf6bfb889797b7d4fe73a");

    // Load or create your User and Item data
    std::vector<User> users;
    std::vector<Item> items;
    std::vector<float> ratings;

    // Train the model
    recommender.train(users, items, ratings);

    // Get recommendations for a user
    User sampleUser;
    auto recommendations = recommender.recommend(sampleUser);

    // Output the recommendations
    for (const auto& item : recommendations) {
        std::cout << "Recommended Item: " << item.getName() << std::endl;
    }

    return 0;
}

