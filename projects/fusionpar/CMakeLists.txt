cmake_minimum_required(VERSION 3.16)
project(fusionpar LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(fusionpar_tb src/fusionpar.cpp tb/fusionpar_tb.cpp)
target_include_directories(fusionpar_tb PRIVATE include)
enable_testing()
add_test(NAME fusionpar_tb COMMAND fusionpar_tb)

# Compile the existing production PR C-model without changing that project.
find_package(Threads REQUIRED)
set(PR_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../persistroute")
add_library(fusionpar_pr_cmodel STATIC
    ${PR_ROOT}/src/pathfinder.cpp
    ${PR_ROOT}/src/accelerated_pathfinder.cpp
    ${PR_ROOT}/src/hbm_cmodel_backend.cpp
    ${PR_ROOT}/src/search_hbm.cpp
    ${PR_ROOT}/src/commit_hbm.cpp
    ${PR_ROOT}/src/multiqueue.cpp)
target_include_directories(fusionpar_pr_cmodel PUBLIC ${PR_ROOT}/include)
target_link_libraries(fusionpar_pr_cmodel PUBLIC Threads::Threads)
add_library(fusionpar_joint STATIC src/joint_state.cpp src/joint_io.cpp src/joint_repair.cpp src/retained_router.cpp)
target_include_directories(fusionpar_joint PUBLIC include)
target_link_libraries(fusionpar_joint PUBLIC fusionpar_pr_cmodel)
target_compile_options(fusionpar_joint PRIVATE -Wall -Wextra -Wpedantic)
add_executable(fusionpar_joint_tb tb/joint_state_tb.cpp)
target_link_libraries(fusionpar_joint_tb PRIVATE fusionpar_joint)
add_test(NAME fusionpar_joint_tb COMMAND fusionpar_joint_tb)
find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(NAME fusionpar_rr_export_cache COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tb/rr_export_cache_test.py)
add_executable(fusionpar_host host/joint_host.cpp)
target_link_libraries(fusionpar_host PRIVATE fusionpar_joint)
