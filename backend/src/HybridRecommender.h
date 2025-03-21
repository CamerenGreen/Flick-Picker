#ifndef HYBRIDRECOMMENDER_H
#define HYBRIDRECOMMENDER_H

#include <vector>
#include <string>

// Forward declarations (assume these classes are defined elsewhere)
class User;
class Item;
class MatrixFactorizationModel;
class ContentBasedModel;

class HybridRecommender {
private:
    MatrixFactorizationModel collaborativeModel;
    ContentBasedModel contentModel;
    std::string apiKey;

    std::vector<Item> combineRecommendations(const std::vector<Item>& recs1, const std::vector<Item>& recs2, int topN);
    std::vector<Item> fetchMovieDetails(const std::vector<std::string>& movieIds);
    std::string fetchFromAPI(const std::string& url);
    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp);

public:
    HybridRecommender(const std::string& key);
    void train(const std::vector<User>& users, const std::vector<Item>& items, const std::vector<float>& ratings);
    std::vector<Item> recommend(const User& user, int topN = 10);
};

#endif // HYBRIDRECOMMENDER_H