#include "speculative_backend.hpp"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <stdexcept>

using namespace dieroute;
using namespace persistroute;
void require(bool v,const char* msg){if(!v)throw std::runtime_error(msg);}
struct Graph {
    std::vector<Node> nodes{9};std::vector<Edge> edges;
    std::vector<Resource> resources=std::vector<Resource>(9,{0,1,256,0,0,INVALID_RESOURCE});
    std::vector<std::uint16_t> owners{0,0,1,1,1,1,1,1,1},members{1,1,3,3,3,2,2,2,2},edge_die;
    std::vector<RRBox> boxes{9};
    Graph() {
        const std::vector<std::vector<unsigned>> adjacent{{2,3},{2,4},{5,6,7,8},{5,6},{7,8},{},{},{},{}};
        for(unsigned n=0;n<9;++n){nodes[n].edge_begin=edges.size();
            for(auto d:adjacent[n]){edges.push_back({d,static_cast<std::uint16_t>(d==3||d==4?100:1),1});
                edge_die.push_back(n<2?0:1);++nodes[n].edge_count;}}
    }
    RRBackendConfig config()const{RRBackendConfig c;c.downstream_cost=true;c.bound_downstream=true;return c;}
    RRBackend serial()const{return RRBackend(nodes,edges,owners,boxes,config(),members,edge_die);}
};
void full_read_journal_and_atomic_commit() {
    Graph g;auto router=g.serial();const Task task{0,7,0,5,0,10,0,0,0};
    const auto before=g.resources;
    auto p=router.propose(g.nodes,g.edges,g.resources,task,{{0,0,0}},false);
    require(std::memcmp(before.data(),g.resources.data(),before.size()*sizeof(Resource))==0,"proposal mutated authority");
    require(p.candidate.path==std::vector<unsigned>({2,5}),"expected cheap proposal");
    require(std::any_of(p.candidate.reads.begin(),p.candidate.reads.end(),[](auto r){return r.resource_id==3;}),
            "unchosen portal read missing from journal");
    ++g.resources[3].version;const auto changed=g.resources;
    require(commit_proposal(g.resources,p,false)==ProposalCommit::stale &&
            std::memcmp(changed.data(),g.resources.data(),changed.size()*sizeof(Resource))==0,
            "off-path stale read must reject entire transaction");
    p=router.propose(g.nodes,g.edges,g.resources,task,{{0,0,0}},false);
    g.resources[5].version=0xffffffffU;
    for(auto& r:p.candidate.reads)if(r.resource_id==5)r.version=0xffffffffU;
    const auto exhausted=g.resources;
    require(commit_proposal(g.resources,p,false)==ProposalCommit::overflow &&
            std::memcmp(exhausted.data(),g.resources.data(),exhausted.size()*sizeof(Resource))==0,
            "late overflow caused partial commit");
    g.resources=before;g.resources[2]={1,1,256,0,1,99};g.resources[3]={1,1,256,0,1,99};
    p=router.propose(g.nodes,g.edges,g.resources,task,{{0,0,0}},false);
    require(p.candidate.search_status==2,"fixture must initially be unreachable");
    g.resources[2].occupancy=0;g.resources[2].owner=INVALID_RESOURCE;++g.resources[2].version;
    require(commit_proposal(g.resources,p,false)==ProposalCommit::stale,"stale failure must be replayed, not accepted");
}
void shadow_messages() {
    BoundaryShadows shadows({0,1},{true,true});
    std::vector<Resource> resources{{0,1,256,0,0,11},{0,1,256,0,0,22}};
    std::vector<WideCost> costs{{256,0},{256,0}};
    shadows.stage(resources,&costs);shadows.publish();
    const ShadowMessage newer{1,1,{1,1,2,1024,300,true}},older{1,1,{1,0,1,512,0,true}};
    require(shadows.receive(0,newer) && !shadows.receive(0,older),"out-of-order shadow delivery regressed state");
    require(!shadows.receive(0,newer),"duplicate message must be idempotent");
    auto view=shadows.view(0,resources,&costs);
    require(view.resource(1).version==2 && view.resource(1).occupancy==1 && view.cost(1)->history_q==300 &&
            view.resource(1).owner==22,"summary must not replace authoritative net owner");
    auto conflict=newer;conflict.value.capacity=2;bool rejected=false;
    try{shadows.receive(0,conflict);}catch(const std::logic_error&){rejected=true;}
    require(rejected && shadows.view(0,resources,&costs).resource(1).capacity==1,"same-version corruption modified shadow");
    resources[1].occupancy=1;rejected=false;
    try{shadows.stage(resources,&costs);}catch(const std::logic_error&){rejected=true;}
    require(rejected,"unversioned owner-state change accepted");
}
void sparse_boundary_storage_and_borrowed_views() {
    constexpr std::size_t count=100000;
    std::vector<std::uint16_t> owners(count,0);owners.back()=1;
    std::vector<bool> boundary(count);boundary[3]=true;boundary.back()=true;
    BoundaryShadows shadows(owners,boundary);
    std::vector<Resource> resources(count,Resource{0,1,256,0,0,INVALID_RESOURCE});
    std::vector<WideCost> costs(count,WideCost{256,0});
    resources.back().owner=91;
    shadows.stage(resources,&costs);shadows.publish();
    auto first=shadows.view(0,resources,&costs);auto second=shadows.view(1,resources,&costs);
    require(shadows.boundary_records()==2&&shadows.summary_records()==6,"shadow summaries must scale with boundary count");
    require(first.overlay_records()==1&&second.overlay_records()==1,"copy only remote boundary records");
    require(first.borrowed_data()==resources.data()&&second.borrowed_data()==resources.data()&&
            &first.resource(50)==&resources[50]&&first.cost(50)==&costs[50],"interior state must be borrowed without a worker copy");
    require(first.resource(count-1).owner==91,"shadow must read the authoritative net owner");
    // Publishing a later summary cannot mutate an already captured overlay.
    // The shared base remains unchanged while these borrowed views are alive.
    shadows.receive(0,{std::uint32_t(count-1),1,{1,1,1,512,3,true}});
    auto later=shadows.view(0,resources,&costs);
    require(first.resource(count-1).version==0&&later.resource(count-1).version==1,
            "captured boundary overlay must remain immutable");
    auto bad=std::make_shared<RRStateOverlay>();(*bad)[count-1]={resources.back(),{256,0}};(*bad)[count-1].resource.owner=92;
    bool rejected=false;try{RRStateView invalid(resources,&costs,bad);}catch(const std::invalid_argument&){rejected=true;}
    require(rejected,"overlay cannot invent a different net owner");
}
void threaded_conflicts_and_delayed_shadows() {
    Graph g;auto serial=g.serial();auto expected=g.resources,actual=g.resources;
    SpeculativeBackend parallel(g.nodes,g.edges,g.owners,g.boxes,g.config(),g.members,g.edge_die,2,10);
    const std::vector<Task> tasks{{0,7,0,5,0,10,0,0,0},{1,8,1,7,0,10,1,0,0}};
    const std::vector<std::vector<SearchSeed>> seeds{{{0,0,0}},{{1,0,0}}};
    for(unsigned window=0;window<3;++window) {
        auto a=serial.execute(g.nodes,g.edges,expected,tasks,seeds,false);
        auto b=parallel.execute(g.nodes,g.edges,actual,tasks,seeds,false);
        for(unsigned i=0;i<2;++i)require(a.candidates[i].path==b.candidates[i].path &&
            a.candidates[i].commit_status==b.candidates[i].commit_status,"speculative replay differs from serial order");
        require(std::memcmp(expected.data(),actual.data(),actual.size()*sizeof(Resource))==0,"authority differs after replay");
        if(window<2)for(unsigned n=0;n<actual.size();++n)if(actual[n].occupancy) {
            actual[n].occupancy=0;actual[n].owner=INVALID_RESOURCE;++actual[n].version;expected[n]=actual[n];
        }
    }
    require(parallel.speculative_metrics().replays>=3 && parallel.speculative_metrics().remote_shadow_reads>0 &&
            parallel.speculative_metrics().maximum_window_tasks==2,"test did not exercise overlap and stale shadows");
}
void complete_controller_equivalence() {
    Graph g;const std::vector<Task> tasks{{0,7,0,5,0,20,0,0,0},{1,7,0,6,0,20,1,0,0},
        {2,8,1,7,0,20,2,0,0},{3,8,1,8,0,20,3,0,0}};
    auto serial=g.serial();WideBatchExecutor base=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over,const auto& c){return serial.execute(n,e,r,t,s,over,&c);};
    PathfinderConfig cfg;cfg.max_iterations=10;
    const auto reference=route_wide_pathfinder(g.nodes,g.edges,g.resources,tasks,base,cfg,4);
    require(reference.result.routing.legal,"serial reference must be legal");
    for(unsigned workers:{1U,2U,4U})for(unsigned sync:{1U,3U})for(unsigned repeat=0;repeat<5;++repeat) {
        SpeculativeBackend router(g.nodes,g.edges,g.owners,g.boxes,g.config(),g.members,g.edge_die,workers,sync);
        WideBatchExecutor exec=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over,const auto& c){return router.execute(n,e,r,t,s,over,&c);};
        auto result=route_wide_pathfinder(g.nodes,g.edges,g.resources,tasks,exec,cfg,4);
        require(result.result.routing.legal && result.result.audit.size()==reference.result.audit.size(),"controller convergence changed");
        for(unsigned i=0;i<result.result.audit.size();++i)require(result.result.audit[i].route_hash==reference.result.audit[i].route_hash &&
            result.result.audit[i].resource_hash==reference.result.audit[i].resource_hash,"shared trees or authoritative costs diverged");
    }
}
void stale_overflow_replays_current_state() {
    Graph g;auto cfg=g.config();cfg.hierarchical=false;cfg.vpr_style_cost=true;
    std::vector<WideCost> costs(9,{256,0});costs[4].present_q=~std::uint64_t(0);
    g.resources[4]={3,1,0,0,1,INVALID_RESOURCE};
    SpeculativeBackend parallel(g.nodes,g.edges,g.owners,g.boxes,cfg,g.members,g.edge_die,2,10);
    auto first=parallel.execute(g.nodes,g.edges,g.resources,{{0,7,0,5,0,20,0,0,0}},{{{0,0,0}}},true,&costs);
    require(first.candidates[0].commit_status==4,"warmup must not read the unsafe remote branch");
    g.resources[4].occupancy=0;g.resources[4].owner=INVALID_RESOURCE;++g.resources[4].version;
    auto expected=g.resources;
    RRBackend serial(g.nodes,g.edges,g.owners,g.boxes,cfg,g.members,g.edge_die);
    const std::vector<Task> tasks{{1,8,1,7,0,20,1,0,0}};
    auto a=serial.execute(g.nodes,g.edges,expected,tasks,{{{1,0,0}}},true,&costs);
    auto b=parallel.execute(g.nodes,g.edges,g.resources,tasks,{{{1,0,0}}},true,&costs);
    require(a.candidates[0].path==b.candidates[0].path && b.candidates[0].commit_status==4 &&
        std::memcmp(expected.data(),g.resources.data(),expected.size()*sizeof(Resource))==0 &&
        parallel.speculative_metrics().replays==1,"stale arithmetic overflow must trigger a fresh replay");
    // Current-state overflow is still fatal and cannot modify authority.
    g.resources[4].occupancy=3;g.resources[4].owner=INVALID_RESOURCE;++g.resources[4].version;
    const auto before=g.resources;
    auto proposal=serial.propose(g.nodes,g.edges,g.resources,tasks[0],{{1,0,0}},true,&costs);
    require(proposal.overflowed && proposal.search_metrics.expanded>0 && commit_proposal(g.resources,proposal,true)==ProposalCommit::overflow &&
        std::memcmp(before.data(),g.resources.data(),before.size()*sizeof(Resource))==0,
        "current overflow must remain fail closed and atomic");
}
int main(){try{full_read_journal_and_atomic_commit();shadow_messages();sparse_boundary_storage_and_borrowed_views();threaded_conflicts_and_delayed_shadows();complete_controller_equivalence();stale_overflow_replays_current_state();
    std::cout<<"speculative_backend_tb PASS\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
