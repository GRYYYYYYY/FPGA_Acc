#include "proposals.hpp"
#include <iostream>
using namespace tileplace_snapshot;
int main() {
    Positions positions{{0,{0,0}},{1,{4,0}},{2,{2,0}}};
    PlacementConstraints constraints;
    for(unsigned i=0;i<3;++i) constraints.blocks[i]={"clb",std::nullopt,{}};
    for(int x=0;x<6;++x) constraints.sites[{x,0}]="clb";
    constraints.reference=positions;
    std::vector<Net> nets{{{0,1},{{0,1,10}}}};
    auto proposals=proposals_for_unit({0},{{0},{1},{2}},{{1}},positions,constraints,nets,
                                     {{0,1,5}},PressureSnapshot({}),{});
    std::set<std::string> kinds;
    for(const auto& p:proposals) {
        if(p.score>=0) throw std::runtime_error("non-improving proposal");
        Positions after=positions; for(const auto& [id,loc]:p.trial) after.at(id)=loc;
        if(!constraints.valid(after)) throw std::runtime_error("illegal proposal");
        kinds.insert(p.kind);
    }
    for(const auto& kind:{"move","swap","chain2"}) if(!kinds.count(kind))
        throw std::runtime_error("expected candidate kind absent");
    auto guarded=proposals_for_unit({0},{{0},{1},{2}},{{1}},positions,constraints,nets,
                                   {{0,1,5}},PressureSnapshot({}),{},{{0,1,0}});
    if(!guarded.empty()) throw std::runtime_error("distance guard ignored");
    auto selected=propose_color(0,{{0},{1},{2}},{{1}},positions,constraints,nets,
                               {{0,1,5}},PressureSnapshot({}),{}, {0});
    if(selected.empty()) throw std::runtime_error("color proposal missing");
    std::set<ProposalIdentity> forbidden{selected.front().identity()};
    auto alternative=propose_color(0,{{0},{1},{2}},{{1}},positions,constraints,nets,
                                  {{0,1,5}},PressureSnapshot({}),{}, {0},forbidden);
    if(alternative.empty() || forbidden.count(alternative.front().identity()))
        throw std::runtime_error("forbidden candidate not suppressed");
    std::cout<<"legal improving moves, swaps, chains and distance guard passed\n";
}
