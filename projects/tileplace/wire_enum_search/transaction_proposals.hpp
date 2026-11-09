// Transitional CPU candidate generator with flat-cost callback; not an HLS kernel.
#pragma once
#include "../hbm_abi/callback_proposals.hpp"
#include "../wire_transactions/encoder_words.hpp"
#include "../wire_best/host_best.hpp"
#include "../wire_dedup/host_dedup.hpp"
#include "../array_costs/score_array.hpp"
#include "../cpp_snapshot/transactions.hpp"

namespace tileplace_snapshot {
struct TransactionColorStats {std::size_t eligible=0,proposals=0,accepted=0,rejected=0;std::map<std::string,std::size_t> kinds;};
template<class Evaluate,class Roots,class Validate,class Translate,class CheckGuard,class Occupy,class SameShape,class Touched,class Writes,class Owners,class Merge,class Chain,class Enumerate>
inline std::vector<Proposal> wire_transaction_proposals_for_unit(const Unit& unit,const std::vector<Unit>& units,
    const std::set<Unit>& fixed,const Positions& positions,const PlacementConstraints& constraints,
    const std::vector<Net>& nets,Evaluate evaluate,Roots roots,Validate valid,Translate translate,CheckGuard guard_ok,Occupy occupy,SameShape same_shape,Touched touched_indices,Writes write_set,Owners classify_owners,Merge merge_trials,Chain build_chain,Enumerate enumerate_trials,
    const CallbackProposalConfig& config,const std::vector<CallbackGuard>& guards={}) {
    (void)guards;
    (void)constraints;
    (void)nets;
    (void)units;(void)positions;(void)roots;(void)translate;(void)occupy;(void)same_shape;(void)classify_owners;(void)merge_trials;(void)build_chain;
    if(unit.empty()) throw std::invalid_argument("empty unit");
    if(fixed.count(unit)) return {};
    std::vector<Proposal> result;
    auto make=[&](std::string kind,std::vector<Unit> moved,Positions trial) {
        auto writes=write_set(trial);
        if(!writes.first || !valid(trial)) return;
        if(!guard_ok(trial))return;
        auto net_ids=touched_indices(trial);
        auto costs=evaluate(net_ids,trial);
        auto scored=tileplace_cost_array::score_array(costs.first.data(),costs.second.data(),config.weights.data());
        if(scored.status==1)throw std::invalid_argument("negative score weight");
        if(scored.status)throw std::overflow_error("transaction score exceeds int64");
        auto score=scored.score;
        if(score>=0) return;
        std::sort(moved.begin(),moved.end());
        result.push_back({std::move(kind),std::move(moved),std::move(trial),std::move(net_ids),std::move(writes.second),score});
    };
    enumerate_trials(unit,make);
    return result;
}
using ProposalIdentity=std::tuple<std::string,std::vector<Unit>,Positions>;
template<class Evaluate,class Roots,class Validate,class Translate,class CheckGuard,class Occupy,class SameShape,class Touched,class Writes,class Owners,class Merge,class Chain,class Enumerate>
inline std::vector<Proposal> wire_transaction_propose_color(unsigned color,const std::vector<Unit>& units,
    const std::set<Unit>& fixed,const Positions& positions,const PlacementConstraints& constraints,
    const std::vector<Net>& nets,Evaluate evaluate,Roots roots,Validate valid,Translate translate,CheckGuard guard_ok,Occupy occupy,SameShape same_shape,Touched touched_indices,Writes write_set,Owners classify_owners,Merge merge_trials,Chain build_chain,Enumerate enumerate_trials,
    const CallbackProposalConfig& config,const std::vector<std::uint32_t>& eligible_indices,
    const std::set<ProposalIdentity>& forbidden={},const std::vector<CallbackGuard>& guards={},TransactionColorStats* stats=nullptr) {
    if(color>=4) throw std::invalid_argument("color out of range");
    TransactionColorStats out;
    std::vector<Proposal> best_candidates;
    for(auto index:eligible_indices) {
        const auto& unit=units.at(index);
        ++out.eligible;
        auto candidates=wire_transaction_proposals_for_unit(unit,units,fixed,positions,constraints,nets,evaluate,roots,valid,translate,guard_ok,occupy,same_shape,touched_indices,write_set,classify_owners,merge_trials,build_chain,enumerate_trials,config,guards);
        auto best=tileplace_wire_best::choose(std::move(candidates),forbidden);
        if(best)best_candidates.push_back(std::move(*best));
    }
    auto proposals=tileplace_wire_dedup::unique(std::move(best_candidates));
    out.proposals=proposals.size();
    auto selected=tileplace_wire_transactions::Encoded(std::move(proposals)).selected();
    out.accepted=selected.size();out.rejected=out.proposals-out.accepted;
    for(const auto& p:selected)++out.kinds[p.kind];
    if(stats)*stats=out;
    return selected;
}
}
