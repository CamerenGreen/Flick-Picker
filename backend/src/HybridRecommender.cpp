#include <pybind11/embed.h>
namespace py = pybind11;

class HybridRecommender {
private:
    py::scoped_interpreter guard{}; // Start the Python interpreter
    py::module_ models;

public:
    HybridRecommender() {
        // Import the Python module
        models = py::module_::import("models.model_bridge");
    }

    void train(const std::vector<User>& users, const std::vector<Item>& items, const std::vector<float>& ratings) {
        // Convert C++ data to Python objects
        py::list py_users, py_items;
        for (const auto& user : users) py_users.append(user.id);
        for (const auto& item : items) py_items.append(item.id);
        py::list py_ratings = py::cast(ratings);

        // Call Python functions
        models.attr("train_mf_model")(py_users, py_items, py_ratings);
        models.attr("train_cb_model")(py_items);
    }

    std::vector<Item> recommend(const User& user, int topN = 10) {
        // Call Python functions
        auto mf_recs = models.attr("predict_mf_model")(user.id, getItemIds());
        auto cb_recs = models.attr("predict_cb_model")(user.viewingHistory, getItemIds(), topN);

        // Combine recommendations
        return combineRecommendations(mf_recs, cb_recs, topN);
    }
};