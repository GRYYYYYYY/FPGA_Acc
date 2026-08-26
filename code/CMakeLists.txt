cmake_minimum_required(VERSION 3.16)
project(fpga_acc_par LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(fpga_acc_router src/router.cpp)
target_include_directories(fpga_acc_router PUBLIC include)
if(MSVC)
    target_compile_options(fpga_acc_router PRIVATE /W4 /permissive-)
else()
    target_compile_options(fpga_acc_router PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_executable(persist_route_sw src/main.cpp)
target_link_libraries(persist_route_sw PRIVATE fpga_acc_router)

enable_testing()
add_executable(router_tests tests/router_tests.cpp)
target_link_libraries(router_tests PRIVATE fpga_acc_router)
add_test(NAME router_tests COMMAND router_tests)
