cmake_minimum_required(VERSION 3.16)
project(routecast LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
add_executable(routecast_tb src/routecast.cpp tb/routecast_tb.cpp)
target_include_directories(routecast_tb PRIVATE include)
enable_testing()
add_test(NAME routecast_tb COMMAND routecast_tb)
add_executable(routecast_contract_tb src/routecast.cpp tests/contract_tb.cpp)
target_include_directories(routecast_contract_tb PRIVATE include)
add_test(NAME routecast_contract_tb COMMAND routecast_contract_tb)
find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(NAME routecast_connection_golden
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_connection_golden.py -v)
add_test(NAME routecast_rr_frontend
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_rr_frontend.py -v)
add_test(NAME routecast_semantic_sketch
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_semantic_sketch.py -v)
add_test(NAME routecast_pre_route_endpoints
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_pre_route_endpoints.py -v)
add_test(NAME routecast_routing_process_labels
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_routing_process_labels.py -v)
add_test(NAME routecast_pin_pools
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_pin_pools.py -v)
add_test(NAME routecast_template_connectivity
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_template_connectivity.py -v)
add_test(NAME routecast_hybrid_repair
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_hybrid_repair.py -v)
add_test(NAME routecast_lazy_region_search
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_lazy_region_search.py -v)
add_test(NAME routecast_blif_constants
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_blif_constants.py -v)
add_test(NAME routecast_pre_route_constants
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_pre_route_constants.py -v)
set_tests_properties(routecast_blif_constants routecast_pre_route_constants
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
add_test(NAME routecast_physical_prediction_audit
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_physical_prediction_audit.py -v)
set_tests_properties(routecast_physical_prediction_audit
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
add_test(NAME routecast_native_node_labels
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_native_node_labels.py -v)
set_tests_properties(routecast_native_node_labels
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
add_test(NAME routecast_regional_search_cache
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_regional_search_cache.py -v)
set_tests_properties(routecast_regional_search_cache
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
add_test(NAME routecast_rr_batch_occupancy
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_rr_batch_occupancy.py -v)
set_tests_properties(routecast_rr_batch_occupancy
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
add_test(NAME routecast_affected_connections
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_affected_connections.py -v)
set_tests_properties(routecast_affected_connections
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
add_test(NAME routecast_feedback_scores
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_feedback_scores.py -v)
set_tests_properties(routecast_feedback_scores
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
add_test(NAME routecast_prepared_templates
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_prepared_templates.py -v)
set_tests_properties(routecast_prepared_templates
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
add_test(NAME routecast_prepared_endpoints
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_prepared_endpoints.py -v)
set_tests_properties(routecast_prepared_endpoints
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
add_test(NAME routecast_timing_context
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_timing_context.py -v)
set_tests_properties(routecast_timing_context
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
add_test(NAME routecast_observed_timing_proxy
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_observed_timing_proxy.py -v)
set_tests_properties(routecast_observed_timing_proxy
 PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")

add_test(NAME routecast_frozen_pressure
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_pressure_sketch.py -v)

add_test(NAME routecast_damped_background
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_damped_background.py -v)

add_test(NAME routecast_scaled_pressure
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_scaled_pressure.py -v)

add_test(NAME routecast_net_pressure
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_net_pressure.py -v)

add_test(NAME routecast_native_indexed_cost
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_native_indexed_cost.py -v)

add_test(NAME routecast_path_rc
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_path_rc.py -v)

add_test(NAME routecast_buffered_rc
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_buffered_rc_sketch.py -v)

add_test(NAME routecast_normalized_rc_base
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_normalized_rc_base.py -v)

add_test(NAME routecast_normalized_rc_pressure
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_normalized_rc_pressure.py -v)

add_test(NAME routecast_normalized_rc_net_pressure
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_normalized_rc_net_pressure.py -v)

add_test(NAME routecast_fast_normalized_rc_net_pressure
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_fast_normalized_rc_net_pressure.py -v)

add_test(NAME routecast_slim_fast_normalized_rc_net_pressure
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_slim_fast_normalized_rc_net_pressure.py -v)

add_test(NAME routecast_tree_reuse
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_tree_reuse.py -v)

add_test(NAME routecast_astar_tree_reuse
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_astar_tree_reuse.py -v)

add_test(NAME routecast_frozen_tree_pressure
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_frozen_tree_pressure.py -v)

add_test(NAME routecast_bound_indexed_cost
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_bound_indexed_cost.py -v)

add_test(NAME routecast_stream_native_route_audit
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_stream_native_route_audit.py -v)

add_test(NAME routecast_cached_bound_rc
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_cached_bound_rc.py -v)

add_test(NAME routecast_stream_metric_domain
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_stream_metric_domain.py -v)

add_test(NAME routecast_exact_goal_astar
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_exact_goal_astar.py -v)

add_test(NAME routecast_prepared_csr
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_prepared_csr.py -v)

add_executable(routecast_csr_consumer tools/csr_consumer/main.cpp)
add_test(NAME routecast_csr_consumer
 COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/tests/check_csr_consumer.py $<TARGET_FILE:routecast_csr_consumer>)

add_test(NAME routecast_predecessor_search
 COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
 -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_predecessor_search.py -v)

add_executable(routecast_csr_predecessor tools/csr_consumer/predecessor_main.cpp)
add_test(NAME routecast_csr_predecessor
 COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/tests/check_csr_consumer.py $<TARGET_FILE:routecast_csr_predecessor>)

add_executable(routecast_indexed_heap_tb tests/indexed_heap_tb.cpp)
target_include_directories(routecast_indexed_heap_tb PRIVATE include)
add_test(NAME routecast_indexed_heap COMMAND routecast_indexed_heap_tb)

add_executable(routecast_csr_fixed_heap tools/csr_consumer/fixed_heap_main.cpp)
target_include_directories(routecast_csr_fixed_heap PRIVATE include)
add_test(NAME routecast_csr_fixed_heap
 COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/tests/check_csr_consumer.py $<TARGET_FILE:routecast_csr_fixed_heap>)

add_executable(routecast_predecessor_path_tb tests/predecessor_path_tb.cpp)
target_include_directories(routecast_predecessor_path_tb PRIVATE include)
add_test(NAME routecast_predecessor_path COMMAND routecast_predecessor_path_tb)

add_executable(routecast_csr_fixed_scratch tools/csr_consumer/fixed_scratch_main.cpp)
target_include_directories(routecast_csr_fixed_scratch PRIVATE include)
add_test(NAME routecast_csr_fixed_scratch
 COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/tests/check_csr_consumer.py $<TARGET_FILE:routecast_csr_fixed_scratch>)

add_executable(routecast_path_transaction_tb tests/path_transaction_tb.cpp)
target_include_directories(routecast_path_transaction_tb PRIVATE include)
add_test(NAME routecast_path_transaction COMMAND routecast_path_transaction_tb)

add_executable(routecast_search_workspace_tb tests/search_workspace_tb.cpp)
target_include_directories(routecast_search_workspace_tb PRIVATE include)
add_test(NAME routecast_search_workspace COMMAND routecast_search_workspace_tb)

add_executable(routecast_workspace_search_tb tests/workspace_search_tb.cpp)
target_include_directories(routecast_workspace_search_tb PRIVATE include)
add_test(NAME routecast_workspace_search COMMAND routecast_workspace_search_tb)

add_executable(routecast_csr_workspace tools/csr_consumer/workspace_main.cpp)
target_include_directories(routecast_csr_workspace PRIVATE include)
add_test(NAME routecast_csr_workspace
 COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/tests/check_csr_consumer.py $<TARGET_FILE:routecast_csr_workspace>)

add_executable(routecast_search_cost_tb tests/search_cost_tb.cpp)
target_include_directories(routecast_search_cost_tb PRIVATE include)
add_test(NAME routecast_search_cost COMMAND routecast_search_cost_tb)

add_executable(routecast_workspace_flat_tb src/workspace_flat.cpp tests/workspace_flat_tb.cpp)
target_include_directories(routecast_workspace_flat_tb PRIVATE include)
add_test(NAME routecast_workspace_flat COMMAND routecast_workspace_flat_tb)

add_executable(routecast_direct_path_tb tests/direct_path_tb.cpp)
target_include_directories(routecast_direct_path_tb PRIVATE include)
add_test(NAME routecast_direct_path COMMAND routecast_direct_path_tb)

add_executable(routecast_direct_heap_tb tests/direct_heap_tb.cpp)
target_include_directories(routecast_direct_heap_tb PRIVATE include)
add_test(NAME routecast_direct_heap COMMAND routecast_direct_heap_tb)

add_executable(routecast_direct_search_tb tests/direct_search_tb.cpp)
target_include_directories(routecast_direct_search_tb PRIVATE include)
add_test(NAME routecast_direct_search COMMAND routecast_direct_search_tb)

add_executable(routecast_csr_direct tools/csr_consumer/direct_main.cpp)
target_include_directories(routecast_csr_direct PRIVATE include)
add_test(NAME routecast_csr_direct
 COMMAND ${Python3_EXECUTABLE} -B ${CMAKE_CURRENT_SOURCE_DIR}/tests/check_csr_consumer.py $<TARGET_FILE:routecast_csr_direct>)

add_executable(routecast_workspace_direct_tb src/workspace_direct.cpp tests/workspace_direct_tb.cpp)
target_include_directories(routecast_workspace_direct_tb PRIVATE include)
add_test(NAME routecast_workspace_direct COMMAND routecast_workspace_direct_tb)

add_executable(routecast_direct_transaction_tb tests/direct_transaction_tb.cpp)
target_include_directories(routecast_direct_transaction_tb PRIVATE include)
add_test(NAME routecast_direct_transaction COMMAND routecast_direct_transaction_tb)

add_executable(routecast_workspace_direct_multisink_tb src/workspace_direct.cpp tests/workspace_direct_multisink_tb.cpp)
target_include_directories(routecast_workspace_direct_multisink_tb PRIVATE include)
add_test(NAME routecast_workspace_direct_multisink COMMAND routecast_workspace_direct_multisink_tb)

# Exact serialized RC and budget-search semantic oracles (host only).
foreach(rc_contract IN ITEMS buffered_rc_node_classes csr_exact_buffered_rc csr_exact_budget_search csr_reverse_delay_bound csr_min_delay_feasibility csr_integer_exact_delay fixed_opin_search)
  add_test(NAME routecast_exact_rc_contract_${rc_contract}
    COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
      -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_${rc_contract}.py -v)
  set_tests_properties(routecast_exact_rc_contract_${rc_contract}
    PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
endforeach()

# Architecture-bound endpoint exclusion; no signal-name inference.
add_test(NAME routecast_nonclock_global_pin_contract
  COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
    -s ${CMAKE_CURRENT_SOURCE_DIR}/tests -p test_nonclock_global_pins.py -v)
set_tests_properties(routecast_nonclock_global_pin_contract
  PROPERTIES ENVIRONMENT "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/tools")
