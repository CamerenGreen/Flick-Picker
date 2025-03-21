cmake_minimum_required(VERSION 3.14)
project(HybridRecommender)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add pybind11 as a subdirectory (if using the submodule approach)
add_subdirectory(pybind11)

# Include pybind11 headers
include_directories(${pybind11_INCLUDE_DIRS})

# Add your source files
set(SOURCES
    src/main.cpp
    src/HybridRecommender.cpp
)

# Add your executable
add_executable(HybridRecommender ${SOURCES})

# Link pybind11
target_link_libraries(HybridRecommender PRIVATE pybind11::module)

# Add Python include directories (for pybind11)
find_package(Python REQUIRED COMPONENTS Development)
target_include_directories(HybridRecommender PRIVATE ${Python_INCLUDE_DIRS})

# Link Python libraries
target_link_libraries(HybridRecommender PRIVATE ${Python_LIBRARIES})