# Array numeric costs

`score_array.hpp` implements Q20 normalized four-cost scoring with signed 128-bit intermediates, Python floor division and explicit negative-weight/delta-overflow/total-overflow statuses. It allocates no containers and throws no exceptions. Five thousand queries match the original checked C++ score behavior (4457 valid/543 rejected), plus explicit negative floor and all three statuses. CMake/CTest passes 1/1. This independent directory preserves running native batch source identities.

Search integration, remaining array network/delta cost calculations and HLS validation are pending. CPU tests do not establish synthesis, resource use or performance.

`ScoredArraySearch` now uses the status-returning Q20 core in the fast transaction candidate path. The host translates error statuses to the existing checked exception behavior. Sixty guarded unit sets, 48 guarded colors and 144 selected-only adapter calls match Python, including all phase statistics and commit/feedback/restore behavior. Independent CTest passes 2/2. Network/delta costs still rely on the earlier host state; full array network costs and native validation of the final integrated path remain pending.
