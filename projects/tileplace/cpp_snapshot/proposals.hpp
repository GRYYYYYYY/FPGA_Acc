#pragma once
#include "placement.hpp"
#include "transactions.hpp"

namespace tileplace_snapshot {
struct ProposalConfig {
    std::int32_t page_width=8,page_height=8;
    std::size_t candidate_limit=24,chain_limit=8;
    std::array<std::int32_t,3> weights{2,2,1};
};
struct Guard {std::uint32_t source,sink; std::uint64_t maximum;};
inline std::vector<Proposal> proposals_for_unit(const Unit& unit,const std::vector<Unit>& units,
    const std::set<Unit>& fixed,const Positions& positions,const PlacementConstraints& constraints,
    const std::vector<Net>& nets,const std::vector<Connection>& routed,const PressureSnapshot& pressure,
    const ProposalConfig& config,const std::vector<Guard>& guards={}) {
    if(unit.empty()) throw std::invalid_argument("empty unit");
    if(fixed.count(unit)) return {};
    std::map<Point,std::uint32_t> occupied;
    std::map<std::uint32_t,Unit> owner_units;
    for(const auto& [id,p]:positions) occupied[p]=id;
    for(const auto& u:units) for(auto id:u) {
        if(!owner_units.emplace(id,u).second) throw std::invalid_argument("overlapping units");
    }
    auto roots=[&](const Unit& u,std::size_t limit) {
        return candidate_roots(positions.at(u.front()),constraints.blocks.at(u.front()).type,
                               constraints.sites,config.page_width,config.page_height,limit);
    };
    using Shape=std::vector<std::pair<std::string,std::array<std::int64_t,4>>>;
    auto shape=[&](const Unit& u) {
        Shape out; auto r=positions.at(u.front());
        for(auto id:u) {auto p=positions.at(id); out.push_back({constraints.blocks.at(id).type,
            {std::int64_t(p.x)-r.x,std::int64_t(p.y)-r.y,std::int64_t(p.subtile)-r.subtile,std::int64_t(p.layer)-r.layer}});}
        std::sort(out.begin(),out.end()); return out;
    };
    std::vector<Proposal> result;
    auto make=[&](std::string kind,std::vector<Unit> moved,Positions trial) {
        Positions candidate=positions; std::set<std::uint32_t> changed;
        bool different=false;
        for(const auto& [id,p]:trial) {candidate.at(id)=p; changed.insert(id); different|=!(positions.at(id)==p);}
        if(!different || !valid_trial(trial,changed,occupied,constraints.blocks,constraints.sites)) return;
        for(const auto& guard:guards) if((changed.count(guard.source)||changed.count(guard.sink)) &&
            distance(candidate.at(guard.source),candidate.at(guard.sink))>guard.maximum) return;
        std::vector<Net> touched; std::set<std::uint32_t> net_ids;
        for(std::size_t i=0;i<nets.size();++i) if(std::any_of(nets[i].members.begin(),nets[i].members.end(),
            [&](auto id){return changed.count(id);})) {touched.push_back(nets[i]); net_ids.insert(i);}
        auto costs=cost_pair(touched,changed,positions,candidate,routed,pressure);
        auto score=transaction_score(costs.first,costs.second,config.weights);
        if(score>=0) return;
        std::set<Point> writes;
        for(auto id:changed) {writes.insert(positions.at(id)); writes.insert(trial.at(id));}
        std::sort(moved.begin(),moved.end());
        result.push_back({std::move(kind),std::move(moved),std::move(trial),std::move(net_ids),std::move(writes),score});
    };
    for(auto target:roots(unit,config.candidate_limit)) {
        auto direct=translated(unit,target,positions); std::set<Unit> owners;
        for(const auto& [id,p]:direct) {
            (void)id; auto found=occupied.find(p);
            if(found!=occupied.end() && std::find(unit.begin(),unit.end(),found->second)==unit.end())
                owners.insert(owner_units.at(found->second));
        }
        if(owners.empty()) {make("move",{unit},direct); continue;}
        if(owners.size()!=1) continue;
        auto other=*owners.begin(); if(other==unit || fixed.count(other)) continue;
        if(unit.size()==other.size() && shape(unit)==shape(other)) {
            auto trial=translated(unit,positions.at(other.front()),positions);
            auto second=translated(other,positions.at(unit.front()),positions);
            trial.insert(second.begin(),second.end());
            make(unit.size()==1?"swap":"macro_swap",{unit,other},trial);
        }
        if(unit.size()!=1 || other.size()!=1) continue;
        for(auto second:roots(other,config.chain_limit)) {
            if(second==positions.at(other.front())) continue;
            auto found=occupied.find(second);
            if(found==occupied.end()) {make("chain2",{unit,other},{{unit.front(),target},{other.front(),second}});continue;}
            auto third=owner_units.at(found->second);
            if(third.size()!=1 || third==unit || third==other || fixed.count(third)) continue;
            make("chain3",{unit,other,third},{{unit.front(),target},{other.front(),second},{third.front(),positions.at(unit.front())}});
        }
    }
    return result;
}
using ProposalIdentity=std::tuple<std::string,std::vector<Unit>,Positions>;
inline std::vector<Proposal> propose_color(unsigned color,const std::vector<Unit>& units,
    const std::set<Unit>& fixed,const Positions& positions,const PlacementConstraints& constraints,
    const std::vector<Net>& nets,const std::vector<Connection>& routed,const PressureSnapshot& pressure,
    const ProposalConfig& config,const std::set<std::uint32_t>& focus,
    const std::set<ProposalIdentity>& forbidden={},const std::vector<Guard>& guards={}) {
    if(color>=4) throw std::invalid_argument("color out of range");
    std::map<ProposalIdentity,Proposal> best_by_id;
    for(const auto& unit:units) {
        if(!focus.empty() && !std::any_of(unit.begin(),unit.end(),[&](auto id){return focus.count(id);})) continue;
        auto p=positions.at(unit.front());
        auto unit_color=((page_coordinate(p.x,config.page_width)&1)<<1)+(page_coordinate(p.y,config.page_height)&1);
        if(unsigned(unit_color)!=color) continue;
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
    return select_transactions(std::move(proposals));
}
}
