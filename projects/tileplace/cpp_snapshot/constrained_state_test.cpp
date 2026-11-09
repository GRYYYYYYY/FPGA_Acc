#include "search_state.hpp"
#include <iostream>
using namespace tileplace_snapshot;
void require(bool v) {if(!v) throw std::runtime_error("constraint transaction failure");}
int main() {
    Positions initial{{0,{0,0}},{1,{1,0}},{2,{3,0}}};
    PlacementConstraints constraints;
    for(unsigned id=0;id<3;++id) constraints.blocks[id]={"clb",std::nullopt,{}};
    for(int x=0;x<6;++x) constraints.sites[{x,0}]="clb";
    constraints.macros={{0,1}}; constraints.reference=initial;
    SearchState state(initial,{{{0,1,2},{{0,2,2}}}},
                      {PressureSnapshot({}),{{0,2,1}},{0}},constraints);
    auto cost=state.cost(0);
    auto feedback=state.feedback();
    auto fails=[&](Positions changes) {
        bool failed=false;
        try {state.begin(changes);} catch(const std::invalid_argument&) {failed=true;}
        require(failed && state.positions()==initial && state.cost(0)==cost && state.feedback()==feedback);
    };
    fails({{0,{1,0}}}); // occupied destination and broken macro
    fails({{0,{1,0}},{1,{3,0}}}); // macro shape and collision
    fails({{0,{4,0}},{1,{6,0}}}); // absent site
    state.begin({{0,{1,0}},{1,{2,0}}});
    require(state.positions().at(0).x==1); state.reject(); require(state.positions()==initial);
    state.begin({{0,{1,0}},{1,{2,0}}}); state.accept();
    require(state.positions().at(1).x==2);
    std::cout<<"constrained begin, macro preservation, atomic failure, accept and rollback passed\n";
}
