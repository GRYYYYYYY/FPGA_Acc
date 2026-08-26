CXX ?= g++
CXXFLAGS += -std=c++17 -O2 -Wall -Wextra -I../include -I$(XILINX_XRT)/include
LDFLAGS += -L$(XILINX_XRT)/lib -lxrt_coreutil -pthread

all: persistroute_pathfinder persistroute_accelerated_cmodel persistroute_accelerated_xrt persistroute_xrt persistroute_multi_xrt

persistroute_pathfinder: pathfinder_host.cpp ../src/pathfinder.cpp ../src/external_timing.cpp
	$(CXX) $(CXXFLAGS) $^ -o $@

persistroute_accelerated_cmodel: accelerated_pathfinder_host.cpp ../src/accelerated_pathfinder.cpp ../src/hbm_cmodel_backend.cpp ../src/search_hbm.cpp ../src/commit_hbm.cpp ../src/multiqueue.cpp ../src/pathfinder.cpp ../src/external_timing.cpp
	$(CXX) $(CXXFLAGS) $^ -o $@

persistroute_accelerated_xrt: accelerated_xrt_host.cpp ../src/accelerated_pathfinder.cpp ../src/pathfinder.cpp ../src/external_timing.cpp
	$(CXX) $(CXXFLAGS) $^ -o $@ $(LDFLAGS)

persistroute_xrt: xrt_host.cpp
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)

persistroute_multi_xrt: multi_pe_xrt_host.cpp
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)

clean:
	rm -f persistroute_pathfinder persistroute_accelerated_cmodel persistroute_accelerated_xrt persistroute_xrt persistroute_multi_xrt
