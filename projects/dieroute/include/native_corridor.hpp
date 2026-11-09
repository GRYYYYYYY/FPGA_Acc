#pragma once
#include "native_route_state.hpp"
#include "native_monotone.hpp"
#include <array>

namespace dieroute {
struct NativePortal {std::uint32_t node, membership, exits;};
enum class NativeFallbackMode {immediate, defer_budget, flat_rescue};
struct NativeCorridorMetrics {
    std::uint64_t plans=0,local_searches=0,flat_searches=0,repairs=0,fallbacks=0;
    std::uint64_t reserved=0,released=0,retained=0,overcapacity=0,ranked=0;
    std::uint64_t cost_prunes=0;
    std::uint64_t joint_searches=0;
    std::uint64_t budget_deferrals=0;
    std::uint64_t joint_expanded=0,joint_edge_visits=0,local_expanded=0,local_edge_visits=0,flat_expanded=0,flat_edge_visits=0;
};
struct NativeCorridorAttempt {
    std::vector<std::uint32_t> dies,portals;
    std::vector<std::uint32_t> path,edges;
    std::uint32_t failed_stage=UINT32_MAX;
    std::uint32_t attachment=UINT32_MAX,hops=0;
    std::uint64_t cost=0;
    bool completed=false,selected=false;
    std::int32_t search_status=-2;
    std::uint64_t expanded=0,edge_visits=0;
    std::vector<SparseSearch::WorkerMetrics> workers;
    std::vector<LabelPacket> packets;
};
// Serial native reference: candidate-local reservations keyed by electrical
// node, never a second mutable occupancy array. Every failed plan discards its
// entire reservation union. NativeRouteState.accept remains the sole publisher.
// Simple die paths and geometry rank proposals only; constrained searches prove
// each segment, and a full-graph fallback preserves the original search scope.
class NativeCorridorRouter {
    std::vector<NativePortal> portals_;
    std::uint32_t dies_,attempts_,portal_candidates_;
    bool compare_reentry_;
    bool bound_reentry_;
    bool joint_portals_;
    bool die_workers_;
    NativeCorridorMetrics metrics_;
    std::vector<NativeCorridorAttempt> trace_;
    static std::uint64_t add(std::uint64_t a,std::uint64_t b){
        if(b>=UINT64_MAX-a)throw std::overflow_error("native corridor cost overflow");
        return a+b;
    }
public:
    NativeCorridorRouter(std::vector<NativePortal> portals,std::uint32_t dies,std::uint32_t attempts,bool compare_reentry=false,bool bound_reentry=false,std::uint32_t portal_candidates=1,bool joint_portals=false,bool die_workers=false)
        :portals_(std::move(portals)),dies_(dies),attempts_(attempts),portal_candidates_(portal_candidates),compare_reentry_(compare_reentry),bound_reentry_(bound_reentry),joint_portals_(joint_portals),die_workers_(die_workers){
        if(die_workers_&&!joint_portals_)throw std::invalid_argument("die workers require joint corridor mode");
        if(!dies || dies>8)throw std::invalid_argument("native corridor die count");
        if(!portal_candidates)throw std::invalid_argument("native corridor candidate count");
        if(joint_portals_&&portal_candidates!=1)throw std::invalid_argument("joint search does not enumerate ranked portal candidates");
        if(joint_portals_)for(auto p:portals_)NativeMonotonePolicy::check_boundary(p.membership);
        std::set<std::uint32_t> seen;
        for(auto p:portals_)if(p.node==UINT32_MAX || !p.membership || p.membership>=(1U<<dies) ||
            !(p.membership&(p.membership-1)) || (p.exits&~p.membership) || !seen.insert(p.node).second)
            throw std::invalid_argument("invalid native portal catalog");
    }
    const auto& metrics()const{return metrics_;}
    const auto& trace()const{return trace_;}
    // expand(node, emit(dst,pip,physical_die)) supplies static-eligible arcs.
    // prepare(goal,cost_ceiling), potential(node) use a consistent relaxation containing
    // every allowed local edge. rank(a,b) is ONLY a deterministic proposal score.
    template<class Expand,class Membership,class Allowed,class Cost,class Prepare,class Potential,class Rank>
    SparseSearchResult run(const NativeRouteState& state,std::uint32_t net,std::uint32_t sink,std::uint32_t sink_die,
        std::uint64_t node_count,SparseSearch& search,SparseSearchLimits limits,
        Expand expand,Membership membership,Allowed allowed,Cost cost,Prepare prepare,Potential potential,Rank rank,
        std::uint64_t& expanded,std::uint64_t& visits,std::size_t& max_labels,NativeFallbackMode fallback_mode=NativeFallbackMode::immediate){
        if(sink_die>=dies_ || !(membership(sink)&(1U<<sink_die)))throw std::invalid_argument("native corridor sink SLR");
        if(fallback_mode!=NativeFallbackMode::immediate&&!joint_portals_)throw std::invalid_argument("budget scheduling requires joint corridor mode");
        if(fallback_mode!=NativeFallbackMode::immediate&&fallback_mode!=NativeFallbackMode::defer_budget&&fallback_mode!=NativeFallbackMode::flat_rescue)throw std::invalid_argument("native fallback mode");
        if(die_workers_&&state.owner_count()!=dies_)throw std::invalid_argument("die worker authority partition mismatch");
        auto node_cost=[&](std::uint32_t node,std::uint32_t die){
            if constexpr(std::is_invocable_v<Cost,std::uint32_t,std::uint32_t>)return cost(node,die);
            else return cost(node);
        };
        trace_.clear();const auto seeds=state.seeds(net);const auto& tree=state.tree(net);
        bool joint_budget_cutoff=false;
        // Count partial work on exceptions as well as ordinary returns.
        struct Work {
            std::uint64_t& expanded;std::uint64_t& visits;std::uint64_t& out_expanded;std::uint64_t& out_visits;
            std::uint64_t before_expanded,before_visits;
            Work(std::uint64_t& e,std::uint64_t& v,std::uint64_t& oe,std::uint64_t& ov):expanded(e),visits(v),out_expanded(oe),out_visits(ov),before_expanded(e),before_visits(v){}
            ~Work(){out_expanded+=expanded-before_expanded;out_visits+=visits-before_visits;}
        };
        std::set<std::uint32_t> banned;std::uint32_t completed_portal_candidates=0;
        bool has_local=false,has_remote=false;
        for(auto s:seeds){has_local|=(membership(s.node)&(1U<<sink_die))!=0;has_remote|=(membership(s.node)&~(1U<<sink_die))!=0;}
        const bool compare=compare_reentry_&&has_local&&has_remote;bool alternate=false,output_selected=false;
        std::optional<SparseSearchResult> best;std::size_t best_reserved=0,best_trace=0;
        struct ReleaseBest {NativeCorridorMetrics& m;std::size_t& size;bool& selected;
            ~ReleaseBest(){if(!selected){m.released+=size;m.retained-=size;}}} release_best{metrics_,best_reserved,output_selected};
        auto local=[&](const std::vector<SparseSeed>& frontier,std::uint32_t goal,std::uint32_t die,const std::set<std::uint32_t>& blocked,bool constrained,std::uint64_t max_cost){
            Work work(expanded,visits,constrained?metrics_.local_expanded:metrics_.flat_expanded,constrained?metrics_.local_edge_visits:metrics_.flat_edge_visits);
            auto bounded=limits;bounded.max_cost=std::min(bounded.max_cost,max_cost);
            prepare(goal,bounded.max_cost);std::set<std::uint32_t> roots;for(auto s:frontier)roots.insert(s.node);
            auto result=search.run_guided(node_count,frontier,goal,UINT32_MAX,[&](std::uint32_t n,auto offer){
                expand(n,[&](std::uint32_t dst,std::uint32_t pip,std::uint32_t physical_die){
                    if(constrained){
                        if(physical_die!=die || !(membership(n)&membership(dst)&(1U<<die)))return;
                        if((blocked.count(dst)||tree.nodes.count(dst))&&!roots.count(dst))return;
                        // A local segment may not consume an unreserved crossing
                        // node as an incidental wire. Its exit portal is explicit.
                        const auto mask=membership(dst);
                        if((mask&(mask-1)) && dst!=goal && !roots.count(dst))return;
                    }
                    offer(dst,pip,[&](){return std::optional<std::uint64_t>(node_cost(dst,constrained?die:UINT32_MAX));});
                });
            },potential,bounded,&expanded,&visits);
            max_labels=std::max(max_labels,search.touched());return result;
        };
        if(fallback_mode==NativeFallbackMode::flat_rescue){
            ++metrics_.fallbacks;++metrics_.flat_searches;
            return local(seeds,sink,0,{},false,UINT64_MAX);
        }
        for(std::uint32_t attempt=0;attempt<attempts_;++attempt){
            ++metrics_.plans;std::array<std::uint32_t,8> parent;parent.fill(UINT32_MAX);
            std::vector<std::uint32_t> queue;
            for(auto s:seeds)for(std::uint32_t d=0;d<dies_;++d)if((!alternate||d!=sink_die)&&(membership(s.node)&(1U<<d)) && parent[d]==UINT32_MAX){parent[d]=d;queue.push_back(d);}
            for(std::size_t pos=0;pos<queue.size() && parent[sink_die]==UINT32_MAX;++pos){
                auto from=queue[pos];
                for(auto p:portals_)if(!banned.count(p.node) && allowed(p.node) && (p.membership&(1U<<from)))
                    for(std::uint32_t to=0;to<dies_;++to)if((p.membership&(1U<<to)) && ((p.exits&(1U<<to))||(joint_portals_&&p.node==sink)) && parent[to]==UINT32_MAX){parent[to]=from;queue.push_back(to);}
            }
            if(parent[sink_die]==UINT32_MAX)break;
            NativeCorridorAttempt record;record.dies.push_back(sink_die);
            const auto before_expanded=expanded,before_visits=visits;
            auto finish_record=[&](){record.expanded=expanded-before_expanded;record.edge_visits=visits-before_visits;};
            while(parent[record.dies.back()]!=record.dies.back())record.dies.push_back(parent[record.dies.back()]);
            std::reverse(record.dies.begin(),record.dies.end());
            std::vector<SparseSeed> frontier;for(auto s:seeds)if(membership(s.node)&(1U<<record.dies.front()))frontier.push_back(s);
            auto estimate=frontier;bool planned=true;std::set<std::uint32_t> reserved;
            for(std::size_t stage=1;!joint_portals_&&stage<record.dies.size();++stage){
                const auto from=record.dies[stage-1],to=record.dies[stage];
                std::uint32_t best=UINT32_MAX;std::uint64_t score=UINT64_MAX;
                for(auto p:portals_){
                    if(banned.count(p.node)||reserved.count(p.node)||!allowed(p.node)||!(p.membership&(1U<<from))||!(p.exits&(1U<<to)))continue;
                    // Reentering a preexisting tree is invalid; a shared portal
                    // already in that tree can instead be a starting seed.
                    if(tree.nodes.count(p.node))continue;
                    ++metrics_.ranked;std::uint64_t prefix=UINT64_MAX;
                    for(auto s:estimate)prefix=std::min(prefix,rank(s.node,p.node));
                    const auto candidate=add(add(prefix,rank(p.node,sink)),node_cost(p.node,from));
                    if(std::tie(candidate,p.node)<std::tie(score,best)){score=candidate;best=p.node;}
                }
                if(best==UINT32_MAX){planned=false;break;}
                record.portals.push_back(best);reserved.insert(best);estimate={{best,0,0}};
            }
            if(!planned)break;
            std::set<std::uint32_t> blocked;SparseSearchResult result;result.status=SparseSearchStatus::found;
            if(joint_portals_){
                // Discover the complete constrained corridor in one search.
                // No capacity is granted during discovery. Its canonical
                // reservation union is recorded only after a complete path.
                ++metrics_.joint_searches;std::vector<std::uint32_t> roots;
                for(auto seed:frontier)roots.push_back(seed.node);
                NativeMonotonePolicy policy(record.dies,roots,sink);
                auto bounded=limits;if(bound_reentry_&&best)bounded.max_cost=std::min(bounded.max_cost,best->cost);
                bool worker_started=false;
                try{
                    Work work(expanded,visits,metrics_.joint_expanded,metrics_.joint_edge_visits);
                    prepare(sink,bounded.max_cost);
                    auto worker=[&](std::uint32_t n){return n==sink?record.dies.back():policy.departure(n,membership(n));};
                    auto expand_worker=[&](std::uint32_t n,auto offer){
                        expand(n,[&](std::uint32_t dst,std::uint32_t pip,std::uint32_t die){
                            if(tree.nodes.count(dst)||!policy.edge(n,dst,membership(n),membership(dst),die))return;
                            if(die_workers_&&worker(n)!=die)throw std::logic_error("worker expanded foreign PIP");
                            offer(dst,pip,[&](){return std::optional<std::uint64_t>(node_cost(dst,die));});
                        });
                    };
                    worker_started=true;
                    if(die_workers_)result=search.run_guided_partitioned(node_count,frontier,sink,UINT32_MAX,dies_,worker,expand_worker,potential,bounded,&expanded,&visits);
                    else result=search.run_guided(node_count,frontier,sink,UINT32_MAX,expand_worker,potential,bounded,&expanded,&visits);
                    if(die_workers_){for(std::uint32_t d=0;d<dies_;++d)record.workers.push_back(search.worker_metrics(d));record.packets=search.packets();}
                    max_labels=std::max(max_labels,search.touched());
                }catch(const std::overflow_error&){if(die_workers_){if(worker_started)record.packets=search.packets();record.workers.clear();for(std::uint32_t d=0;d<dies_;++d)record.workers.push_back(worker_started?search.worker_metrics(d):SparseSearch::WorkerMetrics{});}record.search_status=-1;record.failed_stage=UINT32_MAX-1;finish_record();trace_.push_back(record);throw;}
                metrics_.cost_prunes+=result.status==SparseSearchStatus::cost_limited;
                joint_budget_cutoff|=result.status==SparseSearchStatus::budget_exhausted;
                if(result.status==SparseSearchStatus::found){
                    auto from=result.attachment;
                    for(auto n:result.path){
                        if(n!=sink&&NativeMonotonePolicy::boundary(membership(n)))record.portals.push_back(n);
                        if(n==sink&&policy.departure(from,membership(from))!=record.dies.back())record.portals.push_back(n);
                        from=n;
                    }
                    if(record.portals.size()+1!=record.dies.size())throw std::logic_error("joint corridor transition reconstruction");
                    reserved.insert(record.portals.begin(),record.portals.end());
                }else record.failed_stage=UINT32_MAX-1;
            }
            // An endpoint can itself be a multi-SLR electrical resource even
            // when no explicit die transition is needed in this branch.
            const auto sink_mask=membership(sink);
            if((!joint_portals_||result.status==SparseSearchStatus::found)&&(sink_mask&(sink_mask-1))&&!tree.nodes.count(sink))reserved.insert(sink);
            metrics_.reserved+=reserved.size();
            for(auto n:reserved){const auto it=state.find_use(n);if(it && it->nets.size()>it->nets.count(net))++metrics_.overcapacity;}
            bool retained=false;
            // RAII releases even an overflowed stale attempt before outer replay.
            struct Release {NativeCorridorMetrics& m;std::size_t size;bool& retained;~Release(){if(!retained)m.released+=size;}} release{metrics_,reserved.size(),retained};
            for(std::size_t stage=0;!joint_portals_&&stage<record.dies.size();++stage){
                const auto goal=stage<record.portals.size()?record.portals[stage]:sink;
                ++metrics_.local_searches;SparseSearchResult part;
                const auto ceiling=bound_reentry_&&best?(result.cost<=best->cost?best->cost-result.cost:0):UINT64_MAX;
                try{part=local(frontier,goal,record.dies[stage],blocked,true,ceiling);}
                catch(const std::overflow_error&){record.search_status=-1;record.failed_stage=stage;finish_record();trace_.push_back(record);throw;}
                metrics_.cost_prunes+=part.status==SparseSearchStatus::cost_limited;
                if(part.status!=SparseSearchStatus::found){record.failed_stage=stage;result.status=part.status;break;}
                if(result.attachment==UINT32_MAX)result.attachment=part.attachment;
                result.path.insert(result.path.end(),part.path.begin(),part.path.end());result.edges.insert(result.edges.end(),part.edges.begin(),part.edges.end());
                blocked.insert(part.path.begin(),part.path.end());result.hops=part.hops;result.cost=add(result.cost,part.cost);
                frontier={{goal,part.hops,0}};
            }
            record.search_status=static_cast<std::int32_t>(result.status);finish_record();
            if(result.status==SparseSearchStatus::found){
                record.completed=true;record.path=result.path;record.edges=result.edges;record.attachment=result.attachment;record.hops=result.hops;record.cost=result.cost;
                trace_.push_back(std::move(record));
                if(!best || std::tie(result.cost,result.hops,result.attachment,result.path,result.edges)<std::tie(best->cost,best->hops,best->attachment,best->path,best->edges)){
                    metrics_.released+=best_reserved;metrics_.retained-=best_reserved;
                    best=std::move(result);best_reserved=reserved.size();best_trace=trace_.size()-1;retained=true;metrics_.retained+=reserved.size();
                }
                // The local extension has no portal to diversify. When remote
                // entry comparison is enabled, evaluate it first as before.
                if(compare&&!alternate){alternate=true;continue;}
                // Distinct final portals provide a bounded set of complete
                // proposals. This is not exhaustive over multi-hop corridors:
                // upstream choices still use the deterministic proposal rank.
                // Failed/pruned plans consume the same global attempt budget.
                if(!joint_portals_&&!trace_.back().portals.empty() && ++completed_portal_candidates<portal_candidates_){
                    banned.insert(trace_.back().portals.back());continue;
                }
                break;
            }
            const auto failed=record.failed_stage;trace_.push_back(std::move(record));
            if(joint_portals_){
                if(compare&&!alternate){alternate=true;continue;}
                break;
            }
            if(trace_.back().portals.empty()){
                if(compare&&!alternate){alternate=true;continue;}
                break;
            }
            banned.insert(trace_.back().portals[std::min<std::size_t>(failed,trace_.back().portals.size()-1)]);++metrics_.repairs;
        }
        if(best){trace_.at(best_trace).selected=true;output_selected=true;return std::move(*best);}
        if(fallback_mode==NativeFallbackMode::defer_budget&&joint_budget_cutoff){
            ++metrics_.budget_deferrals;SparseSearchResult deferred;deferred.status=SparseSearchStatus::budget_exhausted;return deferred;
        }
        ++metrics_.fallbacks;++metrics_.flat_searches;
        return local(seeds,sink,0,{},false,UINT64_MAX);
    }
};
} // namespace dieroute
