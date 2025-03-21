#include "HybridRecommender.h"
#include <iostream>
#include <curl/curl.h>
#include <json/json.h>

// Constructor
HybridRecommender::HybridRecommender(const std::string& key) : apiKey(key) {
    // Initialize models here
}

// Train both models
void HybridRecommender::train(const std::vector<User>& users, const std::vector<Item>& items, const std::vector<float>& ratings) {
    collaborativeModel.train(users, items, ratings);
    contentModel.train(items);
}

// Get recommendations from both models
std::vector<Item> HybridRecommender::recommend(const User& user, int topN) {
    auto collaborativeRecommendations = collaborativeModel.predict(user, topN);
    auto contentRecommendations = contentModel.predict(user, topN);
    return combineRecommendations(collaborativeRecommendations, contentRecommendations, topN);
}

// Combine recommendations from both models
std::vector<Item> HybridRecommender::combineRecommendations(const std::vector<Item>& recs1, const std::vector<Item>& recs2, int topN) {
    std::vector<Item> combined;

    // Example combination logic (simplified)
    for (const auto& item : recs1) {
        if (std::find(combined.begin(), combined.end(), item) == combined.end()) {
            combined.push_back(item);
        }
    }

    for (const auto& item : recs2) {
        if (std::find(combined.begin(), combined.end(), item) == combined.end()) {
            combined.push_back(item);
        }
    }

    // Truncate to topN items
    if (combined.size() > topN) {
        combined.resize(topN);
    }

    return combined;
}

// Fetch movie details from TMDB API
std::vector<Item> HybridRecommender::fetchMovieDetails(const std::vector<std::string>& movieIds) {
    std::vector<Item> items;
    for (const auto& id : movieIds) {
        std::string url = "https://api.themoviedb.org/3/movie/" + id + "?api_key=" + apiKey;
        std::string response = fetchFromAPI(url);
        Json::Value root;
        Json::Reader reader;
        if (reader.parse(response, root)) {
            Item item;
            item.id = root["id"].asString();
            item.name = root["title"].asString();
            item.type = "movie";
            for (const auto& genre : root["genres"]) {
                item.genres.push_back(genre["name"].asString());
            }
            items.push_back(item);
        }
    }
    return items;
}

// Fetch data from API using libcurl
std::string HybridRecommender::fetchFromAPI(const std::string& url) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);
    }
    return readBuffer;
}

// Callback function for libcurl
size_t HybridRecommender::WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}