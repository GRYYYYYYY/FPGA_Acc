#include "query_cost_frame.h"
#include <cassert>
#include <cstring>
#include <iostream>
int main() {
    using routecast::QueryCostFrame;
    std::vector<float> costs{2.f,5.f,7.f};const auto before=costs;
    QueryCostFrame f(costs,2,1,{{0,0,routecast::cost_bits(2.f)},{1,1,routecast::cost_bits(5.f)},{2,0,routecast::cost_bits(4.f)}});
    bool rejected=false;try {f.begin(1,0,1);}catch(const routecast::FrameError&) {rejected=true;}
    assert(rejected && !f.active() && std::memcmp(costs.data(),before.data(),costs.size()*4)==0);
    auto token=f.begin(1,1,1);assert(token.generation==1 && costs[0]==2.f && costs[1]==1.f && costs[2]==7.f);f.finish(token);
    assert(std::memcmp(costs.data(),before.data(),costs.size()*4)==0);
    std::cout<<"LATE_PREFLIGHT_HISTORY_REJECTION_IS_ATOMIC_AND_OTHER_NET_STILL_USABLE\n";
}
