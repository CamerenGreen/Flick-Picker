# Flick Picker


**Flick Picker** is a hybrid movie recommendation system that combines **Collaborative Filtering** and **Content-Based Filtering** to provide personalized movie recommendations based on a user's viewing history. The system uses the **TMDB API** to fetch movie details and leverages machine learning models implemented in **PyTorch** for recommendations.

---

## Table of Contents

1. [Features](#features)
2. [Technologies Used](#technologies-used)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Project Structure](#project-structure)
6. [Contributing](#contributing)
7. [License](#license)

---

## Features

- **Hybrid Recommendation Engine**: Combines Collaborative Filtering and Content-Based Filtering for accurate recommendations.
- **TMDB API Integration**: Fetches movie details such as title, genres, and ratings.
- **Machine Learning Models**: Uses PyTorch for implementing Collaborative Filtering and Content-Based Filtering.
- **Chrome Extension**: Provides a user-friendly interface for movie recommendations.
- **Cross-Platform**: Works on Windows, macOS, and Linux.

---

## Technologies Used

- **Backend**:
  - C++ (for core logic)
  - PyTorch (for machine learning models)
  - libcurl (for HTTP requests)
  - jsoncpp (for JSON parsing)
- **Frontend**:
  - Chrome Extension (HTML, CSS, JavaScript)
- **APIs**:
  - TMDB API (for movie data)
- **Build Tools**:
  - CMake (for building the C++ project)
  - pybind11 (for Python-C++ integration)

---

## Installation

### Prerequisites

- **C++ Compiler**: Ensure you have a C++ compiler installed (e.g., MSVC, GCC, or Clang).
- **Python 3.8+**: Required for PyTorch and pybind11.
- **CMake**: Required for building the project.
- **TMDB API Key**: Get your API key from [TMDB](https://www.themoviedb.org/settings/api).

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/CamerenGreen/Flick-Picker.git
   cd Flick-Picker
