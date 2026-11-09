#pragma once
#include "proposals.hpp"
namespace tileplace_snapshot {
struct ColorStats {std::size_t eligible=0,proposals=0,accepted=0,rejected=0;std::map<std::string,std::size_t> kinds;};
inline std::vector<Proposal> propose_color_fast(unsigned color,const std::vector<Unit>& units,
    const std::set<Unit>& fixed,const Positions& positions,const PlacementConstraints& constraints,
    const std::vector<Net>& nets,const std::vector<Connection>& routed,const PressureSnapshot& pressure,
    const ProposalConfig& config,const std::set<std::uint32_t>& focus,
    const std::set<ProposalIdentity>& forbidden={},const std::vector<Guard>& guards={},ColorStats* stats=nullptr) {
    if(color>=4) throw std::invalid_argument("color out of range");
    ColorStats out;
    std::map<ProposalIdentity,Proposal> best_by_id;
    for(const auto& unit:units) {
        if(!focus.empty() && !std::any_of(unit.begin(),unit.end(),[&](auto id){return focus.count(id);})) continue;
        auto p=positions.at(unit.front());
        auto unit_color=((page_coordinate(p.x,config.page_width)&1)<<1)+(page_coordinate(p.y,config.page_height)&1);
        if(unsigned(unit_color)!=color) continue;
        ++out.eligible;
        auto candidates=proposals_for_unit(unit,units,fixed,positions,constraints,nets,routed,pressure,config,guards);
        std::optional<Proposal> best;
        for(auto& candidate:candidates) {
            if(forbidden.count(candidate.identity())) continue;
            if(!best || candidate.score<best->score ||
                (candidate.score==best->score && candidate.identity()<best->identity())) best=std::move(candidate);
        }
        if(best) {
            ProposalIdentity id=best->identity();
            auto old=best_by_id.find(id);
            if(old==best_by_id.end() || best->score<old->second.score) best_by_id.insert_or_assign(id,std::move(*best));
        }
    }
    std::vector<Proposal> proposals;
    for(auto& [id,p]:best_by_id) {(void)id;proposals.push_back(std::move(p));}
    out.proposals=proposals.size();
    auto selected=select_transactions(std::move(proposals));
    out.accepted=selected.size(); out.rejected=out.proposals-out.accepted;
    for(const auto& p:selected) ++out.kinds[p.kind];
    if(stats) *stats=out;
    return selected;
}
}
