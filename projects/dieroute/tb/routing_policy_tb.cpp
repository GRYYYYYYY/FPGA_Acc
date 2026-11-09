#include "speculative_backend.hpp"
#include <cstring>
#include <iostream>
#include <stdexcept>
using namespace dieroute;
using namespace persistroute;
void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
template<class F>void rejects(F f,const char* why){bool caught=false;try{f();}catch(const std::exception&){caught=true;}require(caught,why);}
bool same(const std::vector<Resource>& a,const std::vector<Resource>& b){return a.size()==b.size()&&!std::memcmp(a.data(),b.data(),a.size()*sizeof(Resource));}
struct Graph {
    std::vector<Node> nodes{{0,7,0},{7,1,0},{8,1,0},{9,1,0},{10,1,0},{11,1,0},{12,1,0},{13,0,0},{13,1,0}};
    std::vector<Edge> edges{{1,1,0},{2,2,0},{3,3,0},{4,4,0},{4,10,0},{5,20,0},{6,0,0},
        {7,1,0},{7,1,0},{7,1,0},{7,1,0},{7,1,0},{7,1,0},{3,1,0}};
    std::vector<std::uint16_t> owners{0,1,1,1,1,1,1,1,0},members{1,3,3,3,3,3,3,2,1};
    std::vector<std::uint16_t> edge_die{0,0,0,0,0,0,0,1,1,1,1,1,1,0};
    std::vector<RRBox> boxes{9};
    std::vector<Resource> resources=std::vector<Resource>(9,{0,1,256,0,0,INVALID_RESOURCE});
    std::shared_ptr<RoutingPolicy> policy=std::make_shared<RoutingPolicy>();
    Graph(){policy->node_protection={0,1,2,0,0,0,16,0,0};policy->terminal_net={7,INVALID_RESOURCE,INVALID_RESOURCE,8,INVALID_RESOURCE,7,INVALID_RESOURCE,7,8};
        policy->edge_protection.assign(edges.size(),0);policy->edge_protection[3]=8;
        resources[1]={1,1,9,12,0xffffffffU,99};resources[2].version=resources[6].version=0xffffffffU;}
    RRBackendConfig config(unsigned mode)const{RRBackendConfig c;c.edge_identity=true;c.hierarchical=mode>0;c.downstream_cost=mode>1;c.bound_downstream=mode>2;return c;}
    RRBackend router(unsigned mode,bool enforce=true)const{return RRBackend(nodes,edges,owners,boxes,config(mode),members,edge_die,enforce?policy:RoutingPolicyPtr{});}
    Task task()const{return {0,7,0,7,0,20,0,0,0};}
};
void hard_admission_and_atomicity(){Graph g;
    for(unsigned mode=0;mode<4;++mode){auto r=g.router(mode);auto state=g.resources;
        auto p=r.propose(g.nodes,g.edges,state,g.task(),{{0,0,0}},true);
        require(p.candidate.path==std::vector<unsigned>({4,7})&&p.edge_path==std::vector<unsigned>({4,10}),"search/portal/fallback bypassed hard admission");
        require(p.requires_policy&&same(state,g.resources),"policy proposal metadata or immutability");
        require(commit_proposal(state,p,true,g.nodes,g.edges)==ProposalCommit::invalid&&same(state,g.resources),"policy-aware proposal silently downgraded");
        require(commit_proposal(state,p,true,g.nodes,g.edges,*g.policy)==ProposalCommit::committed,"valid policy proposal failed");
        state=g.resources;auto bad=p;bad.edge_path[0]=3;
        require(commit_proposal(state,bad,true,g.nodes,g.edges,*g.policy)==ProposalCommit::invalid&&same(state,g.resources),"forbidden parallel PIP caused partial writes");
        auto unrestricted=g.router(mode,false);auto fresh=g.resources;fresh[1].version=fresh[2].version=fresh[6].version=0;
        auto illegal=unrestricted.propose(g.nodes,g.edges,fresh,g.task(),{{0,0,0}},true);const auto before=fresh;
        require(!g.policy->path_allowed(illegal.candidate.task,illegal.candidate.attachment,illegal.candidate.path,illegal.edge_path),"negative fixture did not select a forbidden resource");
        require(commit_proposal(fresh,illegal,true,g.nodes,g.edges,*g.policy)==ProposalCommit::invalid&&same(fresh,before),"commit trusted proposal to omit hard policy");
        rejects([&]{r.execute_edges(g.nodes,g.edges,state,{g.task()},{{{0,0,0},{3,0,0}}},true);},"foreign-net terminal seed accepted");
        auto badtask=g.task();badtask.net_id=11;
        rejects([&]{r.execute_edges(g.nodes,g.edges,state,{badtask},{{{0,0,0}}},true);},"foreign-net source terminal accepted");
    }
    auto malformed=std::make_shared<RoutingPolicy>(*g.policy);malformed->edge_protection.pop_back();
    rejects([&]{RRBackend r(g.nodes,g.edges,g.owners,g.boxes,g.config(0),g.members,g.edge_die,malformed);},"truncated policy accepted");
    // A saturated background has no negotiated escape when all usable routes are blocked.
    g.policy->node_protection[4]=g.policy->node_protection[5]=8;
    for(unsigned mode=0;mode<4;++mode){auto r=g.router(mode);auto state=g.resources;
        auto result=r.execute_edges(g.nodes,g.edges,state,{g.task()},{{{0,0,0}}},true);
        require(result.batch.candidates[0].search_status==2&&same(state,g.resources),"overuse bypassed immutable exclusion");}
}
void controller_and_workers(){Graph g;auto tasks=std::vector<Task>{g.task(),{1,8,8,3,0,20,1,0,0}};
    // A second net owns node 3 but cannot be borrowed by net 7, even while ripped up.
    // Connect its two single-SLR terminals in both directions. They remain
    // reserved for net 8 even while that net is temporarily absent from occupancy.
    g.members[3]=1;g.owners[3]=0;g.edge_die[9]=0;g.edges[9]={8,1,0};
    EdgeTimingAnalyzer timing=[](auto,const auto&,const auto&,const auto& routed,const auto&){TimingAnalysisResult x;for(const auto& t:routed)x.connections.push_back({t.task.id,t.task.criticality_q,0,0});return x;};
    PathfinderConfig cfg;cfg.min_timing_iterations=4;
    auto serial=g.router(3);EdgeBatchExecutor base=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over,const auto& c){return serial.execute_edges(n,e,r,t,s,over,&c);};
    auto expected=route_wide_pathfinder_edges(g.nodes,g.edges,g.resources,tasks,base,cfg,4,timing,g.policy);
    require(expected.result.routing.legal&&expected.result.audit.size()==4,"policy controller failed timed rip-up");
    for(unsigned n:{1U,2U,6U}){const auto& a=g.resources[n];const auto& b=expected.result.routing.resources[n];
        require(a.occupancy==b.occupancy&&a.owner==b.owner&&a.version==b.version&&expected.costs[n].present_q==a.present_cost_q&&expected.costs[n].history_q==a.history_cost_q,"protected state or cost changed over epochs");}
    for(unsigned workers:{1U,2U,4U})for(unsigned repeat=0;repeat<5;++repeat){
        SpeculativeBackend spec(g.nodes,g.edges,g.owners,g.boxes,g.config(3),g.members,g.edge_die,workers,3,g.policy);
        EdgeBatchExecutor exec=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over,const auto& c){return spec.execute_edges(n,e,r,t,s,over,&c);};
        auto actual=route_wide_pathfinder_edges(g.nodes,g.edges,g.resources,tasks,exec,cfg,4,timing,g.policy);
        require(actual.result.routing.legal&&actual.task_edges==expected.task_edges&&same(actual.result.routing.resources,expected.result.routing.resources),"policy worker result differs");
        for(unsigned i=0;i<4;++i)require(actual.result.audit[i].route_hash==expected.result.audit[i].route_hash&&actual.result.audit[i].resource_hash==expected.result.audit[i].resource_hash,"policy worker semantic hashes differ");
    }
    // Controller independently rejects an executor that ignored hard admission.
    auto unprotected=g.router(0,false);auto fresh=g.resources;fresh[1].version=fresh[2].version=fresh[6].version=0;
    EdgeBatchExecutor wrong=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over,const auto& c){return unprotected.execute_edges(n,e,r,t,s,over,&c);};
    rejects([&]{route_wide_pathfinder_edges(g.nodes,g.edges,fresh,tasks,wrong,{},4,{},g.policy);},"controller accepted forbidden branch from executor");
}
int main(){try{hard_admission_and_atomicity();controller_and_workers();std::cout<<"routing_policy_tb PASS: hard overuse exclusion, terminal ownership, parallel edge denial, atomic commit, frozen state and costs\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
