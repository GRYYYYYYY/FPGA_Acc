#include "speculative_backend.hpp"
#include <algorithm>
#include <cstring>
#include <iostream>
#include <stdexcept>
using namespace dieroute;
using namespace persistroute;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F> void rejects(F f,const char* message){bool caught=false;try{f();}catch(const std::exception&){caught=true;}require(caught,message);}
bool same(const std::vector<Resource>& a,const std::vector<Resource>& b){return a.size()==b.size()&&!std::memcmp(a.data(),b.data(),a.size()*sizeof(Resource));}
struct Graph {
    std::vector<Node> nodes{{0,2,0},{2,2,0},{4,0,0},{4,0,0}};
    std::vector<Edge> edges{{1,1,90},{1,20,1},{2,1,1},{3,1,1}};
    std::vector<Resource> resources=std::vector<Resource>(4,{0,1,256,0,0,INVALID_RESOURCE});
    std::vector<std::uint16_t> owners{0,1,1,1},members{1,3,2,2},edge_die{0,0,1,1};
    std::vector<RRBox> boxes{4};
    RRBackendConfig config(unsigned mode)const{RRBackendConfig c;c.edge_identity=true;c.hierarchical=mode>0;c.downstream_cost=mode>1;c.bound_downstream=mode>2;return c;}
    RRBackend router(unsigned mode)const{return RRBackend(nodes,edges,owners,boxes,config(mode),members,edge_die);}
    std::vector<Task> tasks(unsigned criticality)const{return {{0,7,0,2,static_cast<std::uint16_t>(criticality),20,0,0,0},{1,7,0,3,static_cast<std::uint16_t>(criticality),20,1,0,0}};}
};
void selection_and_commit() {
    Graph g;
    auto legacy=g.config(0);legacy.edge_identity=false;
    rejects([&]{RRBackend r(g.nodes,g.edges,g.owners,g.boxes,legacy,g.members,g.edge_die);},"legacy native constructor accepted parallel PIPs");
    for(unsigned mode=0;mode<4;++mode){
        auto r=g.router(mode);auto state=g.resources;
        rejects([&]{r.execute(g.nodes,g.edges,state,{g.tasks(65535)[0]},{{{0,0,0}}},false);},"legacy execute discarded selected edges");
        require(same(state,g.resources),"legacy rejection changed state");
        auto p=r.propose(g.nodes,g.edges,state,g.tasks(65535)[0],{{0,0,0}},false);
        require(p.candidate.path==std::vector<unsigned>({1,2})&&p.edge_path==std::vector<unsigned>({1,2}),"parallel PIP selection or zero-hop SLR transition incorrect");
        require(commit_proposal(state,p,false)==ProposalCommit::invalid&&same(state,g.resources),"legacy commit accepted required edge identity");
        auto bad=p;bad.edge_path[0]=2;
        require(commit_proposal(state,bad,false,g.nodes,g.edges)==ProposalCommit::invalid&&same(state,g.resources),"wrong-source edge caused partial commit");
        bad=p;bad.edge_path[1]=3;
        require(commit_proposal(state,bad,false,g.nodes,g.edges)==ProposalCommit::invalid&&same(state,g.resources),"wrong-destination edge caused partial commit");
        bad=p;bad.edge_path.pop_back();
        require(commit_proposal(state,bad,false,g.nodes,g.edges)==ProposalCommit::invalid&&same(state,g.resources),"truncated edge trace accepted");
        bad=p;bad.edge_path[0]=999;
        ++state[p.candidate.reads.front().resource_id].version;const auto stale=state;
        require(commit_proposal(state,bad,false,g.nodes,g.edges)==ProposalCommit::stale&&same(state,stale),"stale rejection must precede trace validation");
        state=g.resources;
        require(commit_proposal(state,p,false,g.nodes,g.edges)==ProposalCommit::committed&&state[1].occupancy==1&&state[2].occupancy==1,"valid edge transaction failed");
        auto batch=r.execute_edges(g.nodes,g.edges,state,{g.tasks(65535)[1]},{{{0,0,0},{1,1,0},{2,2,0}}},false);
        require(batch.edge_paths==std::vector<std::vector<unsigned>>{{3}}&&batch.batch.candidates[0].attachment==1,"shared-tree branch edge trace incorrect");
    }
    // Equal-cost parallel choices deterministically use the lowest CSR edge ID.
    g.edges[1]=g.edges[0];
    for(unsigned mode=0;mode<4;++mode){auto r=g.router(mode);auto state=g.resources;
        auto p=r.propose(g.nodes,g.edges,state,g.tasks(65535)[0],{{0,0,0}},false);
        require(p.edge_path==std::vector<unsigned>({0,2}),"parallel tie break is unstable");}
}
WidePathfinderResult route(Graph& g,unsigned criticality,unsigned workers=0) {
    auto r=g.router(3);SpeculativeBackend spec(g.nodes,g.edges,g.owners,g.boxes,g.config(3),g.members,g.edge_die,workers?workers:1,1);
    EdgeBatchExecutor exec=[&](const auto& n,const auto& e,auto& state,const auto& t,const auto& s,bool over,const auto& c){
        return workers?spec.execute_edges(n,e,state,t,s,over,&c):r.execute_edges(n,e,state,t,s,over,&c);};
    return route_wide_pathfinder_edges(g.nodes,g.edges,g.resources,g.tasks(criticality),exec);
}
void shared_tree_timing_and_hashes() {
    Graph g;
    auto low=route(g,0),high=route(g,65535);
    require(low.result.routing.legal&&high.result.routing.legal,"edge controller failed legal routing");
    require(low.result.routing.tasks[1].path==high.result.routing.tasks[1].path&&low.task_edges[1]!=high.task_edges[1],"fixture must select distinct parallel edges on identical node paths");
    require(low.result.audit.back().route_hash!=high.result.audit.back().route_hash,"route hash omitted selected edge identity");
    require(high.task_edges==std::vector<std::vector<unsigned>>{{1,2},{1,3}}&&high.tree_edges.size()==3,"shared trunk edge must be retained in each task but charged once");
    auto corrupt=high;corrupt.task_edges[1][0]=0;
    require(!validate_wide_edge_result(g.nodes,g.edges,corrupt),"validator accepted conflicting shared trunk PIPs");
    corrupt=high;corrupt.tree_edges.pop_back();
    require(!validate_wide_edge_result(g.nodes,g.edges,corrupt),"validator accepted missing tree edge");
    unsigned timing_calls=0,seed_checks=0;
    auto r=g.router(3);
    EdgeBatchExecutor exec=[&](const auto& n,const auto& e,auto& state,const auto& t,const auto& s,bool over,const auto& c){
        if(t[0].id==1){for(const auto& seed:s[0])if(seed.node==1){++seed_checks;
            require(seed.cost_q==(t[0].epoch?1U:0U),"tree seed timing used first parallel edge instead of selected PIP");}}
        return r.execute_edges(n,e,state,t,s,over,&c);};
    EdgeTimingAnalyzer timing=[&](auto iteration,const auto& n,const auto& e,const auto& tasks,const auto& paths){
        ++timing_calls;TimingAnalysisResult result;
        for(std::size_t i=0;i<tasks.size();++i){require(valid_edge_path(n,e,tasks[i].task.source,tasks[i].path,paths[i]),"timing got disconnected edge trace");
            require(paths[i][0]==(iteration?1U:0U),"timing got stale parallel edge after rip-up");
            result.connections.push_back({tasks[i].task.id,65535,0,0});}return result;};
    PathfinderConfig cfg;cfg.min_timing_iterations=2;cfg.route_tree_timing_weight_q=256;
    auto reroute=route_wide_pathfinder_edges(g.nodes,g.edges,g.resources,g.tasks(0),exec,cfg,4,timing);
    require(reroute.result.routing.legal&&timing_calls==2&&seed_checks==2&&reroute.task_edges==high.task_edges,"edge-aware timing/rip-up did not converge");
    std::uint64_t hashes[2]{};
    for(unsigned i=0;i<2;++i){SpeculativeBackend s(g.nodes,g.edges,g.owners,g.boxes,g.config(3),g.members,g.edge_die,2,1);auto state=g.resources;
        rejects([&]{s.execute(g.nodes,g.edges,state,{g.tasks(i?65535:0)[0]},{{{0,0,0}}},false);},"legacy speculative API discarded edges");
        require(same(state,g.resources),"speculative API rejection changed state");
        s.execute_edges(g.nodes,g.edges,state,{g.tasks(i?65535:0)[0]},{{{0,0,0}}},false);hashes[i]=s.trace().front().path_hash;}
    require(hashes[0]!=hashes[1],"transaction hash omitted selected PIP");
}
void concurrent_replay() {
    Graph g;g.nodes.assign(9,{});g.edges.clear();g.edge_die.clear();g.owners={0,0,1,1,1,1,1,1,1};g.members={1,1,3,3,3,2,2,2,2};
    g.boxes.resize(9);g.resources.assign(9,{0,1,256,0,0,INVALID_RESOURCE});
    const std::vector<std::vector<unsigned>> adjacent{{2,3},{2,4},{5,6,7,8},{5,6},{7,8},{},{},{},{}};
    for(unsigned n=0;n<9;++n){g.nodes[n].edge_begin=g.edges.size();for(auto d:adjacent[n])for(unsigned parallel=0;parallel<2;++parallel){
        g.edges.push_back({d,static_cast<std::uint16_t>((d==3||d==4?100:1)+(!parallel?10:0)),1});g.edge_die.push_back(n<2?0:1);++g.nodes[n].edge_count;}}
    const std::vector<Task> tasks{{0,7,0,5,0,20,0,0,0},{1,8,1,7,0,20,1,0,0}};
    const std::vector<std::vector<SearchSeed>> seeds{{{0,0,0}},{{1,0,0}}};
    auto serial=g.router(3);auto expected=g.resources;auto base=serial.execute_edges(g.nodes,g.edges,expected,tasks,seeds,false);
    std::vector<std::uint64_t> trace_hashes;
    for(unsigned workers:{1U,2U,4U})for(unsigned repeat=0;repeat<5;++repeat){
        SpeculativeBackend spec(g.nodes,g.edges,g.owners,g.boxes,g.config(3),g.members,g.edge_die,workers,1);auto state=g.resources;
        auto actual=spec.execute_edges(g.nodes,g.edges,state,tasks,seeds,false);
        require(same(expected,state)&&actual.edge_paths==base.edge_paths,"replay lost/reused stale edge trace");
        require(actual.batch.candidates[1].path==std::vector<unsigned>({4,7}),"second task failed to reroute around occupied portal");
        require(spec.speculative_metrics().replays==(workers>1?1U:0U),"fixture replay count inconsistent with worker window");
        std::vector<std::uint64_t> hashes;for(const auto& t:spec.trace())hashes.push_back(t.path_hash);
        if(trace_hashes.empty())trace_hashes=hashes;else require(trace_hashes==hashes,"worker count changed edge replay hash");
    }
    // Whole-controller convergence, sharing and final hashes remain independent of workers.
    auto r=g.router(3);EdgeBatchExecutor exec=[&](const auto& n,const auto& e,auto& state,const auto& t,const auto& s,bool over,const auto& c){return r.execute_edges(n,e,state,t,s,over,&c);};
    PathfinderConfig cfg;cfg.max_iterations=10;
    auto reference=route_wide_pathfinder_edges(g.nodes,g.edges,g.resources,tasks,exec,cfg);
    require(reference.result.routing.legal,"parallel-edge reference did not converge");
    for(unsigned workers:{1U,2U,4U})for(unsigned repeat=0;repeat<5;++repeat){
        SpeculativeBackend spec(g.nodes,g.edges,g.owners,g.boxes,g.config(3),g.members,g.edge_die,workers,1);
        EdgeBatchExecutor parallel=[&](const auto& n,const auto& e,auto& state,const auto& t,const auto& s,bool over,const auto& c){return spec.execute_edges(n,e,state,t,s,over,&c);};
        auto result=route_wide_pathfinder_edges(g.nodes,g.edges,g.resources,tasks,parallel,cfg);
        require(result.result.routing.legal&&result.task_edges==reference.task_edges&&result.result.audit.size()==reference.result.audit.size(),"parallel controller edge paths/convergence changed");
        for(unsigned i=0;i<result.result.audit.size();++i)require(result.result.audit[i].route_hash==reference.result.audit[i].route_hash&&result.result.audit[i].resource_hash==reference.result.audit[i].resource_hash,"parallel controller semantic hashes changed");
    }
}
int main(){try{selection_and_commit();shared_tree_timing_and_hashes();concurrent_replay();
    std::cout<<"edge_identity_tb PASS: parallel choice, atomic rejection, shared-tree timing, rip-up, hashes, deterministic replay\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
