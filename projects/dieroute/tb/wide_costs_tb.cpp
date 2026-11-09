#include "rr_backend.hpp"
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
using namespace persistroute;
using namespace dieroute;
void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
void arithmetic_and_rollback() {
    check(grow_present(32768,512)==65536,"present factor crosses u16 boundary exactly");
    check(grow_present(1ULL<<32,512)==1ULL<<33,"present factor crosses u32 boundary exactly");
    bool rejected=false;try{grow_present(~0ULL,512);}catch(const std::overflow_error&){rejected=true;}
    check(rejected,"u64 growth overflow must reject");
    std::vector<Resource> r{{2,1,0,0,9,INVALID_RESOURCE},{1,1,0,0,3,7}};
    std::vector<WideCost> c{{32768,65530},{32768,0}};
    update_wide_costs(r,c,65536,256);
    check(c[0].history_q==65786 && c[0].present_q==65536 && r[0].version==10 && r[1].version==4,
          "wide update increments history and versions exactly once");
    const auto saved_r=r;
    r[1].version=0xffffffffU;const auto original_r=r;const auto original_c=c;
    rejected=false;try{update_wide_costs(r,c,131072,256);}catch(const std::overflow_error&){rejected=true;}
    check(rejected && !std::memcmp(r.data(),original_r.data(),r.size()*sizeof(Resource)) &&
          !std::memcmp(c.data(),original_c.data(),c.size()*sizeof(WideCost)),"last version failure is atomic");
    r=saved_r;c[0].history_q=~0ULL;const auto before=c;
    rejected=false;try{update_wide_costs(r,c,131072,256);}catch(const std::overflow_error&){rejected=true;}
    check(rejected && !std::memcmp(r.data(),saved_r.data(),r.size()*sizeof(Resource)) &&
          !std::memcmp(c.data(),before.data(),c.size()*sizeof(WideCost)),"history overflow is atomic");
    Edge e{0,100,20};Task t{};WideCost high{65536,65792};Resource state{1,1,0,0,0,8};
    check(rr_edge_cost(e,state,t,false,true,&high)==6630600,"wide multiplier affects actual edge cost");
    high={~0ULL,~0ULL};rejected=false;
    try{rr_edge_cost(e,state,t,false,true,&high);}catch(const std::overflow_error&){rejected=true;}
    check(rejected,"cost product cannot wrap even with full u64 fields");
}
void controller_equivalence_and_wide_epochs() {
    std::vector<Node> nodes{{0,1,0},{1,1,0},{2,2,1},{4,0,0},{4,0,0}};
    std::vector<Edge> edges{{1,64,1},{2,64,1},{3,64,1},{4,64,1}};
    std::vector<Resource> initial(5,{0,1,256,0,0,INVALID_RESOURCE});
    std::vector<Task> tasks{{0,7,0,3,32768,20,0,0,0},{1,7,0,4,32768,20,1,0,0}};
    std::vector<std::uint16_t> dies{0,0,1,1,1};std::vector<RRBox> boxes(5);
    for(bool style:{false,true}) {
        RRBackendConfig cfg;cfg.downstream_cost=true;cfg.bound_downstream=true;cfg.vpr_style_cost=style;
        RRBackend legacy(nodes,edges,dies,boxes,cfg),wide_backend(nodes,edges,dies,boxes,cfg);
        KernelBatchExecutor narrow_exec=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool o){return legacy.execute(n,e,r,t,s,o);};
        WideBatchExecutor wide_exec=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool o,const auto& c){return wide_backend.execute(n,e,r,t,s,o,&c);};
        TimingAnalyzer timing=[](auto,const auto&,const auto&,const auto& routed){
            TimingAnalysisResult result;for(const auto& rt:routed)result.connections.push_back({rt.task.id,rt.task.criticality_q,0,0});return result;
        };
        PathfinderConfig cfgp;cfgp.min_timing_iterations=6;
        auto a=route_accelerated_pathfinder(nodes,edges,initial,tasks,narrow_exec,cfgp,4,timing);
        auto b=route_wide_pathfinder(nodes,edges,initial,tasks,wide_exec,cfgp,4,timing);
        check(a.routing.legal && b.result.routing.legal,"both controllers legal");
        check(a.audit.size()==b.result.audit.size(),"same convergence iterations");
        for(std::size_t i=0;i<a.audit.size();++i)check(a.audit[i].resource_hash==b.result.audit[i].resource_hash &&
            a.audit[i].route_hash==b.result.audit[i].route_hash,"logical costs, versions and routes remain identical before overflow");
        for(std::size_t i=0;i<initial.size();++i){auto restored=b.result.routing.resources[i];
            restored.present_cost_q=b.costs[i].present_q;restored.history_cost_q=b.costs[i].history_q;
            check(!std::memcmp(&restored,&a.routing.resources[i],sizeof(Resource)),"split-state reconstruction matches all resource bytes");}
        cfgp.min_timing_iterations=30;
        b=route_wide_pathfinder(nodes,edges,initial,tasks,wide_exec,cfgp,4,timing);
        check(b.result.routing.legal && b.present_factors.size()==30 && b.present_factors.back()==(256ULL<<29),
              "thirty forced epochs preserve factors above u32 without saturation");
        for(const auto& c:b.costs)check(c.present_q==(256ULL<<29) && c.history_q==0,"wide factor persists in authoritative state");
        // Distinct nets forced through one capacity-one trunk cannot converge.
        tasks[1].net_id=8;cfgp.min_timing_iterations=1;cfgp.max_iterations=10;
        b=route_wide_pathfinder(nodes,edges,initial,tasks,wide_exec,cfgp);
        check(!b.result.routing.legal && b.present_factors.back()==131072 && b.costs[2].history_q==9*256,
              "history uses end-of-epoch overuse before rip-up, including beyond u16 growth");
        tasks[1].net_id=7;
    }
}
void only_evaluate_selected_objective() {
    std::vector<Node> nodes{{0,1,0},{1,1,0},{2,1,0},{3,0,0}};
    std::vector<Edge> edges{{1,1,0},{2,64,0},{3,64,0}};
    std::vector<Resource> r(4,{0,1,0,0,0,INVALID_RESOURCE});r[1].occupancy=2;r[1].owner=99;
    std::vector<WideCost> costs(4,{256,0});costs[1].present_q=1ULL<<63;
    RRBackendConfig cfg;cfg.downstream_cost=true;cfg.vpr_style_cost=true;
    RRBackend backend(nodes,edges,{0,0,1,1},std::vector<RRBox>(4),cfg);
    // The additive congestion would overflow, but the selected multiplicative
    // base=1 objective is representable after its declared Q8 scaling.
    auto result=backend.execute(nodes,edges,r,{{0,7,0,3,0,20,0,0,0}},{{{0,0,0}}},true,&costs);
    check(result.candidates[0].commit_status==4,"unselected additive objective must not cause overflow");
}
int main(){try{arithmetic_and_rollback();controller_equivalence_and_wide_epochs();only_evaluate_selected_objective();
    std::cout<<"wide_costs_tb: PASS (64-bit growth, atomic overflow, legacy equivalence, sharing, rip-up)\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
