cmake_minimum_required(VERSION 3.16)
project(tileplace LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
add_executable(tileplace_tb src/tileplace.cpp tb/tileplace_tb.cpp)
target_include_directories(tileplace_tb PRIVATE include)
enable_testing()
add_test(NAME tileplace_tb COMMAND tileplace_tb)
find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(
    NAME tileplace_cpu_golden_tests
    COMMAND ${Python3_EXECUTABLE} -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -v
)
