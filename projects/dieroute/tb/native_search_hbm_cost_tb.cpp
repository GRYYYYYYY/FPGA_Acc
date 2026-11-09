#include "native_search_hbm_cost.hpp"
#include "native_worker_shadows.hpp"
#include <cassert>
#include <random>
using namespace dieroute;
int main(){
 std::mt19937_64 rng(455288);
 for(unsigned i=0;i<10000;++i){auto occupancy=rng()%32,history=rng()%100000,present=rng()%100000;bool own=rng()&1;std::uint64_t cost=0;assert(native_search_observed_cost(occupancy,history,own,present,cost)==NativeSearchCostStatus::ok);assert(cost==NativeWorkerShadows::cost({occupancy,history,7},own,present));}
 std::uint64_t out=123;assert(native_search_observed_cost(2,0,false,UINT64_MAX,out)==NativeSearchCostStatus::overflow&&out==123);
 assert(native_search_observed_cost(0,UINT64_MAX-1,false,0,out)==NativeSearchCostStatus::overflow&&out==123);
 assert(native_search_observed_cost(1,0,true,UINT64_MAX,out)==NativeSearchCostStatus::ok&&out==1);
 assert(native_search_observed_cost(0,UINT64_MAX-2,false,0,out)==NativeSearchCostStatus::ok&&out==UINT64_MAX-1);
}
