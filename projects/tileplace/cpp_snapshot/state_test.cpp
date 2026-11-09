#include "search_state.hpp"
#include <iostream>
using namespace tileplace_snapshot;
void require(bool value) { if(!value) throw std::runtime_error("state invariant failed"); }
int main() {
    Positions placement{{0,{0,0}},{1,{2,0}}};
    Net net{{0,1},{{0,1,3}}};
    Feedback original{PressureSnapshot({{0,0,1,0,9}}),{{0,1,5}},{0}};
    SearchState state(placement,{net},original);
    auto initial=state.cost(0); auto snapshot=state.feedback();
    require(initial[0]==2 && initial[1]==6 && initial[3]==131081);
    state.begin({{1,{1,0}}});
    require(state.cost(0)[0]==1);
    state.replace_feedback({PressureSnapshot({{0,0,1,0,100}}),{{0,1,11}},{1}});
    require(state.cost(0)[3]==65636);
    state.reject();
    require(state.feedback()==snapshot && state.cost(0)==initial);
    require(state.positions().at(1).x==2);
    state.begin({{1,{1,0}}});
    auto candidate=state.cost(0);
    bool rejected=false;
    try { state.replace_feedback({PressureSnapshot({}),{{0,99,1}},{0}}); }
    catch(const std::out_of_range&) { rejected=true; }
    require(rejected && state.feedback()==snapshot && state.cost(0)==candidate);
    state.accept(); require(state.positions().at(1).x==1);
    state.begin({{1,{3,0}}});
    bool nested=false;
    try {state.begin({{1,{4,0}}});} catch(const std::logic_error&) {nested=true;}
    require(nested && state.positions().at(1).x==3);
    state.reject(); require(state.positions().at(1).x==1);
    require(snapshot->pressure.connection({0,0},{2,0})==initial[3]);
    bool overflow=false;
    try {PressureSnapshot p({{0,0,1,0,UINT64_MAX},{1,0,2,0,1}});}
    catch(const std::overflow_error&) {overflow=true;}
    require(overflow);
    std::cout<<"transaction, feedback rollback, cache and overflow checks passed\n";
}
