#include "native_corridor.hpp"
#include <iostream>
#include <random>
using namespace dieroute;
static void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
struct Arc {uint32_t dst,die;};
static auto allowed=[](uint32_t n,uint32_t){return n<32;};
static auto edge=[](uint32_t a,uint32_t b,uint32_t k){return k==a*100+b;};
int main(){try{
    NativeRouteState state;state.start(7,0,allowed);SparseSearch search;
    std::vector<uint32_t> masks(12,1);masks[1]=masks[4]=3;masks[5]=masks[6]=2;
    std::vector<std::vector<Arc>> graph(12);graph[0]={{4,0}};graph[1]={{5,1}};graph[4]={{5,1}};graph[5]={{6,1}};
    auto expand=[&](uint32_t n,auto emit){for(auto a:graph[n])emit(a.dst,n*100+a.dst,a.die);};
    auto member=[&](uint32_t n){return masks.at(n);};auto permit=[](uint32_t){return true;};
    auto cost=[&](uint32_t n){return state.cost(n,7,1);};auto prepare=[](uint32_t,uint64_t){};
    auto zero=[](uint32_t){return uint64_t(0);};auto rank=[](uint32_t,uint32_t){return uint64_t(0);};
    NativeCorridorRouter router({{1,3,2},{4,3,2}},2,3);uint64_t expanded=0,visits=0;size_t labels=0;
    auto result=router.run(state,7,5,1,12,search,{100,UINT64_MAX},expand,member,permit,cost,prepare,zero,rank,expanded,visits,labels);
    check(result.status==SparseSearchStatus::found&&result.path==std::vector<uint32_t>({4,5})&&result.edges==std::vector<uint32_t>({4,405}),"failed portal repaired to exact physical path");
    check(result.cost==2&&result.hops==2&&result.attachment==0,"zero-hop SLR transition adds no synthetic node or cost");
    check(router.metrics().reserved==2&&router.metrics().released==1&&router.metrics().retained==1&&router.metrics().repairs==1,"failed reservation released as a whole");
    check(state.use_count()==1&&state.tree(7).nodes.size()==1,"planning must not mutate authority");
    state.accept(7,5,result,allowed,edge);
    auto next=router.run(state,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,cost,prepare,zero,rank,expanded,visits,labels);
    check(next.path==std::vector<uint32_t>({6})&&next.attachment==5&&next.hops==3,"reuse a shared tree on the destination die");
    state.accept(7,6,next,allowed,edge);check(state.use(4).nets.size()==1&&state.use(4).version==1&&router.metrics().retained==1,"shared SLL reserved/occupied once per net");
    NativeRouteState comparison;comparison.start(7,0,allowed);comparison.accept(7,5,result,allowed,edge);
    masks[7]=masks[8]=2;graph[0]={{1,0},{4,0}};graph[1]={{6,1}};graph[5]={{7,1}};graph[7]={{8,1}};graph[8]={{6,1}};
    auto compare_cost=[&](uint32_t n){return comparison.cost(n,7,1);};
    NativeCorridorRouter keep_local({{1,3,2},{4,3,2}},2,3),compare_entry({{1,3,2},{4,3,2}},2,3,true);
    auto longer=keep_local.run(comparison,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,compare_cost,prepare,zero,rank,expanded,visits,labels);
    auto shorter=compare_entry.run(comparison,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,compare_cost,prepare,zero,rank,expanded,visits,labels);
    check(longer.cost==3&&shorter.cost==2&&shorter.path==std::vector<uint32_t>({1,6}),"complete-cost comparison chooses a better remote entry");
    check(!compare_entry.trace()[0].selected&&compare_entry.trace()[1].selected&&comparison.tree(7).nodes.size()==3,"only selected complete candidate survives; no authority writes");
    NativeCorridorRouter joint_entry({{1,3,2},{4,3,2}},2,3,true,true,1,true);
    auto joint_shorter=joint_entry.run(comparison,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,compare_cost,prepare,zero,rank,expanded,visits,labels);
    check(joint_shorter.cost==shorter.cost&&joint_shorter.path==shorter.path&&joint_entry.metrics().joint_searches==2&&joint_entry.metrics().local_searches==0,"joint complete-cost reentry comparison");
    NativeCorridorRouter tie_entry({{1,3,2},{4,3,2}},2,3,true,true);
    auto tie_cost=[](uint32_t n){return uint64_t(n==1?2:1);};
    auto tie=tie_entry.run(comparison,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,tie_cost,prepare,zero,rank,expanded,visits,labels);
    check(tie.cost==3&&tie.hops==2&&tie.path==std::vector<uint32_t>({1,6}),"bounded comparison retains equal-cost candidate with better full depth");
    graph[5]={{6,1}};graph[1]={{7,1}};
    NativeCorridorRouter reject_entry({{1,3,2},{4,3,2}},2,3,true);
    auto shorter_local=reject_entry.run(comparison,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,compare_cost,prepare,zero,rank,expanded,visits,labels);
    check(shorter_local.cost==1&&shorter_local.path==std::vector<uint32_t>({6})&&reject_entry.metrics().released==1&&reject_entry.metrics().retained==0,"losing complete remote candidate releases reservation");
    NativeCorridorRouter bounded_entry({{1,3,2},{4,3,2}},2,3,true,true);
    auto bounded=bounded_entry.run(comparison,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,compare_cost,prepare,zero,rank,expanded,visits,labels);
    check(bounded.path==shorter_local.path&&bounded_entry.metrics().cost_prunes>0&&bounded_entry.metrics().reserved==bounded_entry.metrics().released,"dominated partial corridor pruned and released");
    masks[6]=3;NativeCorridorRouter throw_after_best({{1,3,2},{4,3,2}},2,3,true);unsigned best_calls=0;bool best_threw=false;
    auto later_overflow=[&](uint32_t){if(++best_calls>1)throw std::overflow_error("after local best");return uint64_t(1);};
    try{throw_after_best.run(comparison,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,later_overflow,prepare,zero,rank,expanded,visits,labels);}catch(const std::overflow_error&){best_threw=true;}
    check(best_threw&&throw_after_best.metrics().reserved==1&&throw_after_best.metrics().released==1&&throw_after_best.metrics().retained==0,"exception releases saved best candidate including multi-SLR terminal");
    NativeCorridorRouter joint_throw({{1,3,2},{4,3,2}},2,3,true,true,1,true);best_calls=0;best_threw=false;
    try{joint_throw.run(comparison,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,later_overflow,prepare,zero,rank,expanded,visits,labels);}catch(const std::overflow_error&){best_threw=true;}
    check(best_threw&&joint_throw.metrics().reserved==1&&joint_throw.metrics().released==1&&joint_throw.metrics().retained==0,"joint overflow releases saved complete candidate; discovery has no early reservation");
    uint64_t thrown_work=0,thrown_visits=0;for(const auto& attempt:joint_throw.trace()){thrown_work+=attempt.expanded;thrown_visits+=attempt.edge_visits;}
    check(joint_throw.trace().back().search_status==-1&&thrown_work==joint_throw.metrics().joint_expanded&&thrown_visits==joint_throw.metrics().joint_edge_visits&&thrown_work>0,"exception records include all partially completed joint search work");
    // A zero-transition local plan cannot realize a necessary die reentry.
    // Fallback must retain that full native path instead of declaring unreachable.
    NativeRouteState reentry;reentry.start(7,0,allowed);
    masks.assign(12,1);masks[1]=masks[4]=3;masks[2]=2;graph.assign(12,{});
    graph[0]={{1,0}};graph[1]={{2,1}};graph[2]={{4,1}};graph[4]={{6,0}};
    NativeCorridorRouter fallback({{1,3,2},{4,3,1}},2,3);
    auto c=[&](uint32_t n){return reentry.cost(n,7,1);};
    auto full=fallback.run(reentry,7,6,0,12,search,{100,UINT64_MAX},expand,member,permit,c,prepare,zero,rank,expanded,visits,labels);
    check(full.status==SparseSearchStatus::found&&full.path==std::vector<uint32_t>({1,2,4,6})&&fallback.metrics().fallbacks==1,"die reentry preserved by fallback");
    NativeCorridorRouter joint_fallback({{1,3,2},{4,3,1}},2,3,false,false,1,true);
    auto joint_full=joint_fallback.run(reentry,7,6,0,12,search,{100,UINT64_MAX},expand,member,permit,c,prepare,zero,rank,expanded,visits,labels);
    check(joint_full.path==full.path&&joint_fallback.metrics().fallbacks==1&&joint_fallback.metrics().reserved==0&&joint_fallback.trace()[0].failed_stage==UINT32_MAX-1,"joint discovery failure keeps unrestricted die-reentry fallback and has no reservation");
    NativeCorridorRouter exhausted_defer({{1,3,2},{4,3,1}},2,3,false,false,1,true);
    auto exhausted_rescue=exhausted_defer.run(reentry,7,6,0,12,search,{100,UINT64_MAX},expand,member,permit,c,prepare,zero,rank,expanded,visits,labels,NativeFallbackMode::defer_budget);
    check(exhausted_rescue.path==full.path&&exhausted_defer.metrics().budget_deferrals==0&&exhausted_defer.metrics().flat_searches==1&&exhausted_defer.trace()[0].search_status==1,"proven exhaustion still falls back immediately under budget deferral mode");
    // Both endpoint memberships contain die 1, but the physical PIP is on die 0.
    // Checking membership alone would incorrectly accept the constrained tail.
    masks.assign(12,1);masks[1]=masks[3]=3;masks[2]=2;graph.assign(12,{});
    graph[0]={{1,0}};graph[1]={{3,0},{2,1}};
    NativeCorridorRouter physical({{1,3,3},{3,3,0}},2,1);
    auto p=physical.run(reentry,7,3,1,12,search,{100,UINT64_MAX},expand,member,permit,c,prepare,zero,rank,expanded,visits,labels);
    check(p.status==SparseSearchStatus::found&&physical.trace().at(0).failed_stage==1&&physical.metrics().fallbacks==1&&physical.metrics().released==2,"physical PIP SLR checked before local acceptance");
    // Current-budget failure has no hidden reservation or partial tree write.
    NativeCorridorRouter budget({{1,3,3},{3,3,0}},2,1);
    auto fail=budget.run(reentry,7,3,1,12,search,{1,UINT64_MAX},expand,member,permit,c,prepare,zero,rank,expanded,visits,labels);
    check(fail.status==SparseSearchStatus::budget_exhausted&&budget.metrics().released==budget.metrics().reserved&&reentry.use_count()==1,"budget rejection releases reservations without mutation");
    // A throw after reservation must also release it before outer shadow replay.
    NativeCorridorRouter overflow({{1,3,3},{3,3,0}},2,1);bool threw=false;unsigned calls=0;
    auto overflow_cost=[&](uint32_t){if(++calls>1)throw std::overflow_error("injected local overflow");return uint64_t(1);};
    try{overflow.run(reentry,7,3,1,12,search,{100,UINT64_MAX},expand,member,permit,overflow_cost,prepare,zero,rank,expanded,visits,labels);}catch(const std::overflow_error&){threw=true;}
    check(threw&&overflow.metrics().reserved==2&&overflow.metrics().released==2&&reentry.use_count()==1,"overflow releases candidate reservation");
    // The first geometrically ranked portal is feasible but expensive. Compare
    // complete alternatives rather than stopping at that first feasible path.
    NativeRouteState alternatives;alternatives.start(7,0,allowed);
    masks.assign(12,1);masks[1]=masks[4]=masks[9]=3;masks[6]=2;graph.assign(12,{});
    graph[0]={{1,0},{4,0},{9,0}};graph[1]={{6,1}};graph[4]={{6,1}};graph[9]={{6,1}};
    auto proposal_rank=[](uint32_t a,uint32_t b){return uint64_t(a==1||b==1?0:10);};
    auto proposal_cost=[](uint32_t n){return uint64_t(n==1?3:1);};
    NativeCorridorRouter first({{1,3,2},{4,3,2},{9,3,2}},2,8),multi({{1,3,2},{4,3,2},{9,3,2}},2,8,false,true,3);
    auto run_alternative=[&](NativeCorridorRouter& r){return r.run(alternatives,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,proposal_cost,prepare,zero,proposal_rank,expanded,visits,labels);};
    auto first_result=run_alternative(first),multi_result=run_alternative(multi);
    check(first_result.cost==4&&multi_result.cost==2&&multi_result.path==std::vector<uint32_t>({4,6}),"complete portal comparison improves first feasible proposal");
    check(multi.trace().size()==3&&multi.trace()[1].selected&&multi.trace()[2].completed&&!multi.trace()[2].selected,"equal-cost portal remains eligible and deterministic tie wins");
    check(multi.metrics().reserved==3&&multi.metrics().released==2&&multi.metrics().retained==1&&alternatives.tree(7).nodes.size()==1,"all losing complete portal reservations released without authority writes");
    NativeCorridorRouter one_attempt({{1,3,2},{4,3,2},{9,3,2}},2,1,false,true,3),two_candidates({{1,3,2},{4,3,2},{9,3,2}},2,8,false,true,2);
    check(run_alternative(one_attempt).path==first_result.path&&one_attempt.trace().size()==1,"candidate exploration obeys global attempt limit");
    check(run_alternative(two_candidates).path==multi_result.path&&two_candidates.trace().size()==2,"complete candidate limit stops exploration");
    // A dominated remaining candidate can be pruned without discarding the
    // already verified winner or failing the branch.
    NativeCorridorRouter prune_loser({{1,3,2},{4,3,2},{9,3,2}},2,8,false,true,3);
    auto dominated_cost=[](uint32_t n){return uint64_t(n==1?3:n==9?8:1);};
    auto winner=prune_loser.run(alternatives,7,6,1,12,search,{100,UINT64_MAX},expand,member,permit,dominated_cost,prepare,zero,proposal_rank,expanded,visits,labels);
    check(winner.path==multi_result.path&&prune_loser.metrics().cost_prunes>0&&prune_loser.metrics().reserved==prune_loser.metrics().released+1,"pruned last proposal retains valid winner and releases loser");
    // Independent exhaustive oracle over four disjoint physical corridors.
    // Vary prefix/suffix lengths, costs, and proposal ordering; a complete
    // attempt budget must recover the best full path despite cost pruning.
    std::mt19937 rng(20261013);
    for(unsigned trial=0;trial<500;++trial){
        graph.assign(32,{});masks.assign(32,1);masks[31]=2;
        std::vector<uint64_t> weights(32),ranks(32);
        for(unsigned n=0;n<32;++n){weights[n]=1+rng()%7;ranks[n]=rng()%20;}
        std::vector<NativePortal> catalog;SparseSearchResult oracle;oracle.cost=UINT64_MAX;
        for(unsigned i=0;i<4;++i){
            auto base=1+5*i,portal=base+2;catalog.push_back({portal,3,2});masks[portal]=3;
            std::vector<uint32_t> path;auto prefix=rng()%3,suffix=rng()%3;
            for(unsigned j=0;j<prefix;++j)path.push_back(base+j);
            path.push_back(portal);
            for(unsigned j=0;j<suffix;++j){path.push_back(base+3+j);masks[base+3+j]=2;}
            path.push_back(31);std::vector<uint32_t> edges;uint32_t from=0,die=0;uint64_t path_cost=0;
            for(auto dst:path){graph[from].push_back({dst,die});edges.push_back(from*100+dst);path_cost+=weights[dst];if(dst==portal)die=1;from=dst;}
            auto hops=uint32_t(path.size());
            if(std::tie(path_cost,hops,path,edges)<std::tie(oracle.cost,oracle.hops,oracle.path,oracle.edges)){
                oracle.cost=path_cost;oracle.hops=hops;oracle.path=path;oracle.edges=edges;
            }
        }
        NativeCorridorRouter enumerated(catalog,2,4,false,true,4);
        auto actual=enumerated.run(alternatives,7,31,1,32,search,{100,UINT64_MAX},expand,member,permit,
            [&](uint32_t n){return weights[n];},prepare,zero,[&](uint32_t a,uint32_t b){return ranks[a]+ranks[b];},expanded,visits,labels);
        check(actual.status==SparseSearchStatus::found&&actual.cost==oracle.cost&&actual.hops==oracle.hops&&actual.path==oracle.path&&actual.edges==oracle.edges,"complete bounded portal enumeration agrees with exhaustive path oracle");
        check(enumerated.metrics().reserved==enumerated.metrics().released+1&&enumerated.metrics().retained==1&&enumerated.metrics().fallbacks==0,"random portal candidate reservations conserved");
        NativeCorridorRouter joint(catalog,2,1,false,false,1,true);
        auto all=joint.run(alternatives,7,31,1,32,search,{100,UINT64_MAX},expand,member,permit,
            [&](uint32_t n){return weights[n];},prepare,zero,[&](uint32_t a,uint32_t b){return ranks[a]+ranks[b];},expanded,visits,labels);
        check(all.status==SparseSearchStatus::found&&all.cost==oracle.cost&&all.hops==oracle.hops,"one joint search agrees with exhaustive complete-portal oracle cost and hops");
        check(joint.metrics().joint_searches==1&&joint.metrics().ranked==0&&joint.metrics().reserved==1&&joint.metrics().retained==1,"joint discovery records only the selected physical reservation");
    }
    graph.assign(32,{});masks.assign(32,1);masks[1]=3;graph[0]={{1,0}};
    NativeCorridorRouter terminal_joint({{1,3,0}},2,1,false,false,1,true);
    auto terminal_path=terminal_joint.run(alternatives,7,1,1,32,search,{100,UINT64_MAX},expand,member,permit,c,prepare,zero,rank,expanded,visits,labels);
    check(terminal_path.path==std::vector<uint32_t>({1})&&terminal_joint.trace()[0].portals==std::vector<uint32_t>({1})&&terminal_joint.metrics().fallbacks==0,"joint terminal portal needs no outgoing PIP on sink die");
    NativeCorridorRouter joint_budget({{1,3,0}},2,1,false,false,1,true);
    auto joint_failed=joint_budget.run(alternatives,7,1,1,32,search,{1,UINT64_MAX},expand,member,permit,c,prepare,zero,rank,expanded,visits,labels);
    check(joint_failed.status==SparseSearchStatus::budget_exhausted&&joint_budget.metrics().reserved==0&&joint_budget.metrics().fallbacks==1,"joint budget failure releases no uncreated reservation and remains distinct from exhaustion");
    NativeCorridorRouter defer({{1,3,0}},2,1,false,false,1,true);const auto before_work=expanded,before_edges=visits;
    auto deferred=defer.run(alternatives,7,1,1,32,search,{1,UINT64_MAX},expand,member,permit,c,prepare,zero,rank,expanded,visits,labels,NativeFallbackMode::defer_budget);
    check(deferred.status==SparseSearchStatus::budget_exhausted&&defer.metrics().budget_deferrals==1&&defer.metrics().flat_searches==0&&defer.trace()[0].search_status==2,"budget deferral does not immediately repeat full-graph work");
    check(defer.metrics().joint_expanded==expanded-before_work&&defer.metrics().joint_edge_visits==visits-before_edges&&defer.trace()[0].expanded==defer.metrics().joint_expanded,"partial joint work is attributed to its attempt");
    auto rescued=defer.run(alternatives,7,1,1,32,search,{100,UINT64_MAX},expand,member,permit,c,prepare,zero,rank,expanded,visits,labels,NativeFallbackMode::flat_rescue);
    check(rescued.path==terminal_path.path&&defer.trace().empty()&&defer.metrics().joint_searches==1&&defer.metrics().flat_searches==1&&defer.metrics().plans==1,"explicit stalled-tree rescue skips the already failed constrained search");
    check(defer.metrics().joint_expanded+defer.metrics().flat_expanded==expanded-before_work&&defer.metrics().joint_edge_visits+defer.metrics().flat_edge_visits==visits-before_edges,"joint and rescue work sum to all actual work");
    std::cout<<"native corridor repair, shared-tree deduplication, PIP die, reentry fallback, bounded portal comparisons, budget and overflow tests passed\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
