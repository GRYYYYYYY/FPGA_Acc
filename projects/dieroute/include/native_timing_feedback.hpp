#pragma once
#include "native_route_state.hpp"
#include <optional>
#include <sstream>
#include <string>
#include <tuple>

namespace dieroute {
// Exact serialization, not a probabilistic hash. Timing binds to all selected
// trees; the context identifies fixed outside routing, constraints and mapping.
inline std::string native_tree_identity(const NativeRouteState& state){
    std::ostringstream out;
    for(const auto& [net,t]:state.trees())for(const auto& [n,v]:t.nodes)
        out<<net<<' '<<n<<' '<<v.parent<<' '<<v.pip<<' '<<v.depth<<'\n';
    return out.str();
}
enum class NativeTimingKind {setup,hold};
enum class NativeTimingCoverage {finite,unconstrained,missing};
struct NativeTimingKey {
    std::uint32_t load,net;
    NativeTimingKind kind;
    bool operator<(const NativeTimingKey& b)const{return std::tie(load,net,kind)<std::tie(b.load,b.net,b.kind);}
};
struct NativeTimingValue {
    NativeTimingCoverage coverage;
    std::optional<std::int64_t> slack_ps;
};
struct NativeTimingSnapshot {
    std::string context,trees;
    std::uint64_t epoch=0;
    std::map<NativeTimingKey,NativeTimingValue> loads;
};
struct NativeTimingPolicy {
    std::int64_t setup_floor_ps=0,hold_floor_ps=0;
    // Unconstrained coverage must be explicit and stable. This never establishes
    // full-design timing acceptance, even when the selected-load gate passes.
    bool allow_reported_unconstrained=false;
};
struct NativeTimingDecision {
    bool selected_scope_accepted=false;
    std::string reason;
    std::set<std::uint32_t> violating_nets;
    std::size_t setup_violations=0,hold_violations=0,unconstrained=0;
};

class NativeTimingController {
    NativeRouteState authority_;
    NativeTimingSnapshot timing_;
    NativeTimingPolicy policy_;
    static void require(bool ok,const char* what){if(!ok)throw std::logic_error(what);}
    static void validate_shape(const NativeTimingSnapshot& timing,const NativeRouteState& state){
        require(!timing.context.empty()&&!timing.loads.empty(),"empty timing context/coverage");
        require(timing.trees==native_tree_identity(state),"timing belongs to different route trees");
        require(state.overused()==0,"timing candidate electrically overused");
        std::map<std::uint32_t,std::pair<std::uint32_t,unsigned>> loads;
        std::set<std::uint32_t> nets;
        for(const auto& [k,v]:timing.loads){
            require(k.load!=UINT32_MAX&&state.trees().count(k.net),"unknown timing load/net");nets.insert(k.net);
            const unsigned bit=k.kind==NativeTimingKind::setup?1:k.kind==NativeTimingKind::hold?2:0;
            require(bit!=0,"invalid timing kind");
            auto [it,inserted]=loads.emplace(k.load,std::make_pair(k.net,0u));(void)inserted;
            require(it->second.first==k.net&&!(it->second.second&bit),"inconsistent timing load identity");it->second.second|=bit;
            require(v.coverage==NativeTimingCoverage::finite||v.coverage==NativeTimingCoverage::unconstrained||v.coverage==NativeTimingCoverage::missing,
                    "invalid timing coverage");
            require(v.slack_ps.has_value()==(v.coverage==NativeTimingCoverage::finite),"invalid finite/missing slack");
        }
        for(const auto& [id,value]:loads){(void)id;require(value.second==3,"missing setup/hold observation");}
        require(nets.size()==state.trees().size(),"timing does not cover every selected net");
    }
    NativeTimingDecision evaluate(const NativeTimingSnapshot& timing)const{
        NativeTimingDecision result;
        for(const auto& [k,v]:timing.loads){
            if(v.coverage==NativeTimingCoverage::missing){result.reason="missing_path";return result;}
            if(v.coverage==NativeTimingCoverage::unconstrained){
                ++result.unconstrained;
                if(!policy_.allow_reported_unconstrained){result.reason="unconstrained_path";return result;}
                continue;
            }
            auto floor=k.kind==NativeTimingKind::setup?policy_.setup_floor_ps:policy_.hold_floor_ps;
            if(*v.slack_ps<floor){result.violating_nets.insert(k.net);
                if(k.kind==NativeTimingKind::setup)++result.setup_violations;else ++result.hold_violations;}
        }
        result.selected_scope_accepted=result.violating_nets.empty();
        result.reason=result.selected_scope_accepted?"selected_scope_pass":"slack_floor";return result;
    }
public:
    NativeTimingController(NativeRouteState state,NativeTimingSnapshot timing,NativeTimingPolicy policy)
        :authority_(std::move(state)),timing_(std::move(timing)),policy_(policy){
        require(policy.setup_floor_ps>=0&&policy.hold_floor_ps>=0,"negative timing policy floor");
        validate_shape(timing_,authority_);
        require(evaluate(timing_).selected_scope_accepted,"baseline fails selected timing policy");
    }
    const NativeRouteState& authority()const{return authority_;}
    std::uint64_t epoch()const{return timing_.epoch;}
    NativeTimingDecision consider(const NativeRouteState& candidate,const NativeTimingSnapshot& timing){
        require(authority_.layout().same(candidate.layout()),"timing candidate changed authority layout");
        validate_shape(timing,candidate);
        require(timing_.epoch!=UINT64_MAX&&timing.epoch==timing_.epoch+1,"stale/exhausted timing epoch");
        require(timing.context==timing_.context,"timing context changed");
        require(timing.loads.size()==timing_.loads.size(),"timing coverage changed");
        for(const auto& [k,v]:timing.loads){auto old=timing_.loads.find(k);
            require(old!=timing_.loads.end()&&old->second.coverage==v.coverage,"timing key/coverage changed");}
        require(candidate.trees().size()==authority_.trees().size(),"candidate net set changed");
        for(const auto& [net,t]:authority_.trees())
            require(candidate.trees().count(net)&&candidate.tree(net).source==t.source,"candidate source changed");
        auto decision=evaluate(timing);
        if(decision.selected_scope_accepted){
            // All allocations precede publication; no partial rollback is needed.
            NativeRouteState staged(candidate);NativeTimingSnapshot next(timing);
            authority_.swap(staged);timing_.context.swap(next.context);timing_.trees.swap(next.trees);
            timing_.loads.swap(next.loads);timing_.epoch=next.epoch;
        }
        return decision;
    }
};

struct NativeTimingRepair {
    NativeRouteState candidate;
    std::set<std::uint32_t> restored_nets;
    // Always requires a fresh oracle for the complete new candidate.
    bool requires_native_timing=true;
};
template<class Allowed,class EdgeValid>
NativeTimingRepair restore_native_timing_nets(const NativeRouteState& baseline,
                                            const NativeRouteState& proposal,
                                            std::set<std::uint32_t> restore,
                                            Allowed allowed,EdgeValid edge_valid){
    auto require=[](bool ok,const char* what){if(!ok)throw std::logic_error(what);};
    require(baseline.overused()==0&&proposal.overused()==0,"repair requires conflict-free endpoints");
    require(baseline.trees().size()==proposal.trees().size(),"repair net set changed");
    for(const auto& [net,t]:baseline.trees())
        require(proposal.trees().count(net)&&proposal.tree(net).source==t.source,"repair source changed");
    for(auto net:restore)require(baseline.trees().count(net),"repair unknown net");
    // Compute conflict closure before touching even the private copy. Restoring
    // an original tree may occupy resources used by another proposed net.
    std::vector<std::uint32_t> queue(restore.begin(),restore.end());
    for(std::size_t i=0;i<queue.size();++i)for(const auto& [n,v]:baseline.tree(queue[i]).nodes){
        (void)v;auto u=proposal.find_use(n);if(!u)continue;
        for(auto net:u->nets)if(restore.insert(net).second)queue.push_back(net);
    }
    NativeTimingRepair result{proposal,restore,true};
    for(auto net:restore)result.candidate.ripup(net);
    for(auto net:restore){
        const auto& tree=baseline.tree(net);
        std::vector<std::pair<std::uint32_t,std::uint32_t>> order;
        for(const auto& [n,v]:tree.nodes)if(n!=tree.source)order.emplace_back(v.depth,n);
        std::sort(order.begin(),order.end());
        for(const auto& [depth,n]:order){const auto& v=tree.nodes.at(n);
            SparseSearchResult branch;branch.status=SparseSearchStatus::found;branch.attachment=v.parent;
            branch.hops=depth;branch.path={n};branch.edges={v.pip};
            result.candidate.accept(net,n,branch,allowed,edge_valid);
        }
    }
    require(result.candidate.overused()==0,"repair closure left resource conflicts");return result;
}
} // namespace dieroute
