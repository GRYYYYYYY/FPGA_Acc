#include "rr_backend.hpp"
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <tuple>
#include <random>

using namespace persistroute;
using dieroute::RRBackend;
using dieroute::RRBackendConfig;
void require(bool x, const char* text) { if (!x) throw std::runtime_error(text); }
struct Fixture {
    std::vector<Node> nodes;
    std::vector<Edge> edges;
    std::vector<Resource> resources;
    std::vector<std::uint16_t> dies;
    std::vector<dieroute::RRBox> boxes;
    Fixture(std::vector<std::uint16_t> die, std::vector<std::pair<unsigned,unsigned>> arcs):dies(die) {
        nodes.resize(die.size()); boxes.resize(die.size());
        resources.assign(die.size(),{0,1,256,0,0,INVALID_RESOURCE});
        std::sort(arcs.begin(),arcs.end());
        for(unsigned n=0;n<nodes.size();++n) {
            nodes[n].edge_begin=edges.size();
            for(auto [a,b]:arcs)if(a==n){edges.push_back({b,64,1});++nodes[n].edge_count;}
        }
    }
};
void multi_hop_sharing() {
    Fixture f({0,0,1,1,2,2,2},{{0,1},{1,2},{2,3},{3,4},{4,5},{4,6}});
    RRBackend backend(f.nodes,f.edges,f.dies,f.boxes);
    KernelBatchExecutor executor=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool o) {
        return backend.execute(n,e,r,t,s,o);
    };
    const std::vector<Task> tasks{{0,7,0,5,0,30,0,0,0},{1,7,0,6,0,30,1,0,0}};
    const auto result=route_accelerated_pathfinder(f.nodes,f.edges,f.resources,tasks,executor);
    require(result.routing.legal,"three-die multi-sink native PR validation");
    require(result.routing.tasks[0].path==std::vector<unsigned>({1,2,3,4,5}),"three-die path");
    require(result.routing.tasks[1].path==std::vector<unsigned>({1,2,3,4,6}),"shared trunk retained");
    for(unsigned n=1;n<7;++n)require(result.routing.resources[n].occupancy==1,"same-net sharing counted once");
    require(backend.metrics().committed_crossings==2 && backend.metrics().reserved_resources==4 &&
            backend.metrics().committed_corridors==1 && backend.metrics().fallbacks==0,"multi-hop reservation metrics");
}
void repair_and_rollback() {
    // The cheapest portal's source cannot be reached from the connection source.
    // Both portal alternatives alias the exact same destination RR resource.
    // An unreachable cycle prevents a trivial SOURCE-root proof, so the detailed
    // local search must still reject and repair this portal.
    Fixture f({0,0,0,1,1,0,0},{{0,2},{1,3},{2,3},{3,4},{5,6},{6,1},{1,5}});
    f.boxes[2]={5,0,5,0};
    RRBackend backend(f.nodes,f.edges,f.dies,f.boxes);
    auto resources=f.resources;
    Task t{0,8,0,4,0,20,0,0,0};
    auto batch=backend.execute(f.nodes,f.edges,resources,{t},{{{0,0,0}}},false);
    require(batch.candidates[0].commit_status==4,"alternate portal commits");
    require(batch.candidates[0].path==std::vector<unsigned>({2,3,4}),"repair picks reachable portal");
    require(backend.metrics().repairs==1 && backend.metrics().aborted_reservations==2 &&
            backend.metrics().reserved_resources==4 && backend.metrics().fallbacks==0,"failed reservation released");
    require(resources[1].occupancy==0 && resources[1].version==0 && resources[3].occupancy==1,
            "aborted source unchanged; aliased destination counted once");
    resources=f.resources;t.max_hops=1;
    batch=backend.execute(f.nodes,f.edges,resources,{t},{{{0,0,0}}},false);
    require(batch.candidates[0].commit_status!=4,"hop budget failure");
    require(std::memcmp(resources.data(),f.resources.data(),resources.size()*sizeof(Resource))==0,"failed local and fallback searches leave state unchanged");
    resources=f.resources;resources[4].version=0xffffffffU;const auto original=resources;
    t.max_hops=20;bool rejected=false;
    try{backend.execute(f.nodes,f.edges,resources,{t},{{{0,0,0}}},false);}catch(const std::overflow_error&){rejected=true;}
    require(rejected && std::memcmp(resources.data(),original.data(),resources.size()*sizeof(Resource))==0,
            "late commit overflow leaves entire path unchanged");
}
void leave_and_reenter_die() {
    Fixture f({0,1,0},{{0,1},{1,2}});
    RRBackend backend(f.nodes,f.edges,f.dies,f.boxes);
    auto r=f.resources;
    auto batch=backend.execute(f.nodes,f.edges,r,{{0,1,0,2,0,20,0,0,0}},{{{0,0,0}}},false);
    require(batch.candidates[0].path==std::vector<unsigned>({1,2}) && batch.candidates[0].commit_status==4,
            "complete fallback supports non-simple die traversal");
    require(backend.metrics().fallbacks==1,"fallback is counted");
}
void source_root_filter() {
    Fixture f({0,0,0,1,1},{{0,2},{1,3},{2,3},{3,4}});
    f.boxes[2]={5,0,5,0};
    RRBackend backend(f.nodes,f.edges,f.dies,f.boxes);auto r=f.resources;
    auto out=backend.execute(f.nodes,f.edges,r,{{0,8,0,4,0,20,0,0,0}},{{{0,0,0}}},false);
    require(out.candidates[0].commit_status==4 && backend.metrics().repairs==0 &&
            backend.metrics().structurally_pruned_portals>0,"prove foreign SOURCE portal unreachable before reserving");
    // Arbitrary internal task sources must not be rejected by a SOURCE-only proof.
    RRBackend internal(f.nodes,f.edges,f.dies,f.boxes);r=f.resources;
    out=internal.execute(f.nodes,f.edges,r,{{0,8,2,4,0,20,0,0,0}},{{{2,0,0}}},false);
    require(out.candidates[0].commit_status==4,"internal task source retains reachable portal");
}
void deterministic_capacity() {
    Fixture f({0,0,1,1,1},{{0,2},{1,2},{2,3},{2,4}});
    f.resources[2].capacity=2;
    const std::vector<Task> tasks{{4,3,0,3,0,20,9,0,0},{1,5,1,4,0,20,2,0,0}};
    for(unsigned repeat=0;repeat<5;++repeat) {
        RRBackend backend(f.nodes,f.edges,f.dies,f.boxes);auto r=f.resources;
        auto out=backend.execute(f.nodes,f.edges,r,tasks,{{{0,0,0}},{{1,0,0}}},false);
        require(out.candidates[0].task.id==1 && out.candidates[1].task.id==4,"fixed priority commit order");
        require(r[2].occupancy==2 && r[2].version==2 && r[2].owner==INVALID_RESOURCE,"shared capacity across distinct nets");
        require(out.candidates[0].commit_status==4 && out.candidates[1].commit_status==4,"capacity two accepts both nets");
    }
    f.resources[2].capacity=1;
    RRBackend backend(f.nodes,f.edges,f.dies,f.boxes);auto r=f.resources;
    auto out=backend.execute(f.nodes,f.edges,r,tasks,{{{0,0,0}},{{1,0,0}}},false);
    require(out.candidates[0].commit_status==4 && out.candidates[1].commit_status!=4 && r[2].occupancy==1,
            "aliased portals do not fabricate capacity");
}
void downstream_delay_selection() {
    Fixture f({0,0,0,1,1,1},{{0,1},{0,2},{1,3},{2,4},{3,5},{4,5}});
    f.edges[f.nodes[3].edge_begin].delay_q=50000;
    const Task t{0,7,0,5,65535,20,0,0,0};
    RRBackend geometric(f.nodes,f.edges,f.dies,f.boxes);auto r=f.resources;
    auto a=geometric.execute(f.nodes,f.edges,r,{t},{{{0,0,0}}},false);
    require(a.candidates[0].path==std::vector<unsigned>({1,3,5}),"geometry ignores slow downstream edge");
    RRBackendConfig cfg;cfg.downstream_cost=true;
    RRBackend aware(f.nodes,f.edges,f.dies,f.boxes,cfg);r=f.resources;
    auto b=aware.execute(f.nodes,f.edges,r,{t},{{{0,0,0}}},false);
    require(b.candidates[0].path==std::vector<unsigned>({2,4,5}),"downstream delay changes portal selection");
    require(aware.metrics().downstream_searches==1 && aware.metrics().downstream_expanded>0 &&
            b.search_metrics.expanded>=aware.metrics().downstream_expanded,"lookahead work included in total");
    // Congestion on the downstream path changes the decision even at zero criticality.
    Fixture g({0,0,0,1,1,1,1,1},{{0,1},{0,2},{1,3},{2,4},{3,6},{6,5},{4,7},{7,5}});
    g.resources[6].occupancy=1;g.resources[6].owner=99;
    g.resources[6].history_cost_q=20000;
    RRBackend congested(g.nodes,g.edges,g.dies,g.boxes,cfg);r=g.resources;
    auto low=t;low.criticality_q=0;
    b=congested.execute(g.nodes,g.edges,r,{low},{{{0,0,0}}},true);
    require(b.candidates[0].path==std::vector<unsigned>({2,4,7,5}),"downstream non-portal congestion is included");
}
void shared_tree_reentry_comparison() {
    Fixture f({0,1,0,1,1,1},{{0,1},{0,2},{2,3},{1,4},{4,5},{3,5}});
    f.edges[f.nodes[1].edge_begin].delay_q=50000;
    f.resources[1].owner=7;f.resources[1].occupancy=1;
    const Task task{1,7,0,5,65535,20,0,0,0};
    const std::vector<std::vector<SearchSeed>> seeds{{{0,0,0},{1,1,0}}};
    RRBackend geometric(f.nodes,f.edges,f.dies,f.boxes);auto r=f.resources;
    auto a=geometric.execute(f.nodes,f.edges,r,{task},seeds,false);
    require(a.candidates[0].attachment==1 && a.candidates[0].path==std::vector<unsigned>({4,5}),"minimum die-hop policy keeps costly existing entry");
    RRBackendConfig cfg;cfg.downstream_cost=true;
    RRBackend comparison(f.nodes,f.edges,f.dies,f.boxes,cfg);r=f.resources;
    a=comparison.execute(f.nodes,f.edges,r,{task},seeds,false);
    require(a.candidates[0].attachment==0 && a.candidates[0].path==std::vector<unsigned>({2,3,5}),"compare existing entry with cheaper new corridor");
    require(r[1].occupancy==1 && r[4].occupancy==0 && comparison.metrics().committed_corridors==1,"losing local candidate does not mutate state");
}
void bounded_downstream_equivalence() {
    std::mt19937 random(20261013);
    for(unsigned trial=0;trial<1000;++trial) {
        std::vector<std::pair<unsigned,unsigned>> arcs;
        for(unsigned a=0;a<12;++a)for(unsigned b=0;b<12;++b)
            if(a!=b && random()%7==0)arcs.push_back({a,b});
        Fixture f({0,0,0,0,0,0,1,1,1,1,1,1},arcs);
        for(auto& edge:f.edges){edge.base_cost_q=random()%128;edge.delay_q=random()%256;}
        for(auto& state:f.resources){state.history_cost_q=random()%256;state.occupancy=random()%2;state.owner=state.occupancy?99:INVALID_RESOURCE;}
        RRBackendConfig full;full.downstream_cost=true;full.vpr_style_cost=(trial/2)%2;
        auto bounded=full;bounded.bound_downstream=true;
        RRBackend a(f.nodes,f.edges,f.dies,f.boxes,full),b(f.nodes,f.edges,f.dies,f.boxes,bounded);
        Task t{trial,7,0,11,static_cast<std::uint16_t>(random()),20,0,0,0};
        const bool over=trial%2;
        std::vector<SearchSeed> seeds{{0,0,0}};
        // Vary existing tree attachment costs and permit seeds on the target
        // die too, exercising the local-versus-new-corridor comparison.
        if(trial%3)for(unsigned node:{1U,6U}) {
            seeds.push_back({node,1,static_cast<std::uint32_t>(random()%4000)});
            f.resources[node].owner=7;f.resources[node].occupancy=1;
        }
        auto r1=f.resources,r2=f.resources;
        std::vector<dieroute::WideCost> wide;
        if(trial%3==0)for(std::size_t i=0;i<f.resources.size();++i)
            wide.push_back({std::uint64_t(random()%65536)<<24,random()%16777216U});
        const auto* costs=wide.empty()?nullptr:&wide;
        auto out1=a.execute(f.nodes,f.edges,r1,{t},{seeds},over,costs);
        auto out2=b.execute(f.nodes,f.edges,r2,{t},{seeds},over,costs);
        const auto& c1=out1.candidates[0];const auto& c2=out2.candidates[0];
        require(c1.attachment==c2.attachment && c1.path==c2.path && c1.commit_status==c2.commit_status,
                "bounded reverse frontier must preserve exact selected branch");
        require(std::memcmp(r1.data(),r2.data(),r1.size()*sizeof(Resource))==0,"bounded lookahead state equivalence");
        require(b.metrics().downstream_expanded<=a.metrics().downstream_expanded,"cutoff cannot expand more than full reverse search");
    }
}
void multiplicative_cost_reference() {
    Resource r{0,1,256,0,0,INVALID_RESOURCE};
    Edge e{0,100,20};Task t{};
    require(dieroute::rr_edge_cost(e,r,t,false,true)==100,"uncongested static base cost");
    r.occupancy=1;r.history_cost_q=256;
    require(dieroute::rr_edge_cost(e,r,t,false,true)==400,"base times history times present");
    t.criticality_q=32768;
    require(dieroute::rr_edge_cost(e,r,t,false,true)==209,"criticality blends congestion and delay with declared floors");
    t.criticality_q=65535;
    require(dieroute::rr_edge_cost(e,r,t,false,true)==20,"criticality one selects delay only");
    require(dieroute::rr_edge_cost(e,r,t,false,false)==632,"legacy additive arithmetic remains unchanged");
    t.criticality_q=0;
    require(dieroute::rr_edge_cost(e,r,t,true,true)==100,"owned resource skips congestion multiplier");
    // Compare the decomposition against independently evaluated extrema. The
    // raw triple product is larger than u64, so direct multiplication is wrong.
    r.occupancy=65535;r.capacity=0;r.history_cost_q=65535;r.present_cost_q=65535;e.base_cost_q=65535;
    require(dieroute::rr_edge_cost(e,r,t,false,true)==282561586921214ULL,"maximum u16 operands do not wrap");
}
void criticality_changes_corridor_objective() {
    Fixture f({0,0,0,1,1,1},{{0,1},{0,2},{1,3},{2,4},{3,5},{4,5}});
    f.edges[f.nodes[3].edge_begin]={5,400,0};
    f.edges[f.nodes[4].edge_begin]={5,100,300};
    Task t{0,7,0,5,49151,20,0,0,0};
    for(bool flat:{false,true})for(bool bounded:{false,true})for(bool style:{false,true}) {
        RRBackendConfig cfg;cfg.hierarchical=!flat;cfg.downstream_cost=true;cfg.bound_downstream=bounded;cfg.vpr_style_cost=style;
        RRBackend backend(f.nodes,f.edges,f.dies,f.boxes,cfg);auto r=f.resources;
        const auto out=backend.execute(f.nodes,f.edges,r,{t},{{{0,0,0}}},false);
        require(out.candidates[0].commit_status==4 && out.candidates[0].path==
            (style?std::vector<unsigned>({1,3,5}):std::vector<unsigned>({2,4,5})),
            "all search modes must apply the same timing/congestion objective");
    }
}
void upstream_tree_delay() {
    // The first sink forces a slow cross-die trunk. A second sink can reuse it
    // with one new edge or build a faster, two-edge branch from the root.
    Fixture f({0,1,0,1,1},{{0,1},{0,2},{1,3},{1,4},{2,4}});
    f.edges[f.nodes[0].edge_begin].delay_q=2000;
    for(bool flat:{false,true})for(bool bounded:{false,true})for(unsigned weight:{0U,256U})for(unsigned criticality:{0U,65535U}) {
        RRBackendConfig cfg;cfg.hierarchical=!flat;cfg.downstream_cost=true;cfg.bound_downstream=bounded;
        RRBackend backend(f.nodes,f.edges,f.dies,f.boxes,cfg);
        bool observed_upstream_cost=false;
        KernelBatchExecutor executor=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool o) {
            if(t[0].id==1)for(const auto& seed:s[0])if(seed.node==1) {
                require(seed.cost_q==((weight && criticality)?2000U:0U),"controller passes upstream delay to RR backend");
                observed_upstream_cost=true;
            }
            return backend.execute(n,e,r,t,s,o);
        };
        PathfinderConfig controller;controller.route_tree_timing_weight_q=weight;
        const std::vector<Task> tasks{{0,7,0,3,65535,20,0,0,0},{1,7,0,4,static_cast<std::uint16_t>(criticality),20,1,0,0}};
        auto result=route_accelerated_pathfinder(f.nodes,f.edges,f.resources,tasks,executor,controller);
        require(result.routing.legal && observed_upstream_cost,"shared-tree timing experiment legal");
        require(result.routing.tasks[0].path==std::vector<unsigned>({1,3}),"forced trunk retained for first sink");
        require(result.routing.tasks[1].path==((weight && criticality)?std::vector<unsigned>({2,4}):std::vector<unsigned>({1,4})),
                "upstream seed delay must change second sink's attachment");
        require(result.routing.resources[1].occupancy==1,"shared trunk occupancy remains per net");
    }
}
void portal_seed_delay() {
    // Both existing source-die tree branches touch an exit. Ignoring seed cost
    // ranks the slow exit first even though its upstream delay is much larger.
    Fixture f({0,0,0,1,1,1},{{0,1},{0,2},{1,3},{2,4},{3,5},{4,5}});
    f.boxes[0]={100,0,100,0};f.boxes[2]={10,0,10,0};
    f.resources[1].owner=7;f.resources[1].occupancy=1;
    f.resources[2].owner=7;f.resources[2].occupancy=1;
    f.edges[f.nodes[0].edge_begin].delay_q=2000;
    const Task task{0,7,0,5,65535,20,0,0,0};
    for(bool bounded:{false,true}) {
        RRBackendConfig cfg;cfg.downstream_cost=true;cfg.bound_downstream=bounded;
        RRBackend backend(f.nodes,f.edges,f.dies,f.boxes,cfg);auto r=f.resources;
        auto out=backend.execute(f.nodes,f.edges,r,{task},{{{0,0,0},{1,1,2000},{2,1,1}}},false);
        require(out.candidates[0].attachment==2 && out.candidates[0].path==std::vector<unsigned>({4,5}),
                "portal estimate must include the chosen seed's upstream timing cost");
    }
}
void native_membership_resource_identity() {
    // PIPs live on dies 0 and 1, but node 1 is ONE electrical resource.
    // Its authoritative owner can be either member without changing routing.
    for(unsigned owner : {0U,1U}) for(bool flat : {false,true}) for(bool bounded : {false,true}) {
        Fixture f({0,static_cast<std::uint16_t>(owner),1,0,1,0},
                  {{0,1},{1,2},{1,3},{1,5},{4,1}});
        const std::vector<std::uint16_t> membership{1,3,2,1,2,1}, edge_die{0,1,0,0,1};
        RRBackendConfig cfg;cfg.hierarchical=!flat;cfg.downstream_cost=true;cfg.bound_downstream=bounded;
        RRBackend backend(f.nodes,f.edges,f.dies,f.boxes,cfg,membership,edge_die);
        auto r=f.resources;
        auto batch=backend.execute(f.nodes,f.edges,r,{{0,7,0,2,0,2,0,0,0}},{{{0,0,0}}},false);
        require(batch.candidates[0].commit_status==4 && batch.candidates[0].path==std::vector<unsigned>({1,2}),
                "internal SLR transition adds no path entry or hop");
        require(r[1].occupancy==1 && r[1].version==1,"one physical capacity/version across SLRs");
        if(!flat) require(backend.metrics().reserved_resources==1 && backend.metrics().fallbacks==0,
                          "native corridor reserves one canonical resource");
        const auto before=r;
        batch=backend.execute(f.nodes,f.edges,r,{{1,8,4,5,0,2,1,0,0}},{{{4,0,0}}},false);
        require(batch.candidates[0].commit_status!=4 && std::memcmp(before.data(),r.data(),r.size()*sizeof(Resource))==0,
                "opposite-SLR access cannot bypass physical capacity");
        // Both PIPs in die 0: merely touching a multi-SLR node does not require a corridor.
        RRBackend local(f.nodes,f.edges,f.dies,f.boxes,cfg,membership,edge_die);r=f.resources;
        batch=local.execute(f.nodes,f.edges,r,{{0,7,0,3,0,2,0,0,0}},{{{0,0,0}}},false);
        require(batch.candidates[0].commit_status==4 && local.metrics().committed_corridors==0 &&
                local.metrics().fallbacks==0,"local traversal uses PIP die, not representative owner");
    }
}
void native_membership_tree_and_validation() {
    Fixture f({0,0,1,2,2},{{0,1},{1,2},{2,3},{2,4}});
    const std::vector<std::uint16_t> membership{1,3,6,4,4}, edge_die{0,1,2,2};
    RRBackendConfig cfg;cfg.downstream_cost=true;cfg.bound_downstream=true;
    RRBackend backend(f.nodes,f.edges,f.dies,f.boxes,cfg,membership,edge_die);
    KernelBatchExecutor executor=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& seeds,bool over) {
        return backend.execute(n,e,r,t,seeds,over);
    };
    auto result=route_accelerated_pathfinder(f.nodes,f.edges,f.resources,
        {{0,7,0,3,0,3,0,0,0},{1,7,0,4,0,3,1,0,0}},executor);
    require(result.routing.legal && result.routing.tasks[1].path==std::vector<unsigned>({1,2,4}),
            "native membership retains PR full route-tree semantics");
    for(unsigned n=1;n<5;++n)require(result.routing.resources[n].occupancy==1,"shared native trunk counted once");
    require(backend.metrics().fallbacks==0,"three-die native corridor requires no flat fallback");
    for(unsigned bad=0;bad<4;++bad) {
        auto m=membership,d=edge_die;
        if(bad==0)m[1]=1; // PIP in die 1 lacks source membership.
        if(bad==1)d[0]=2; // Neither endpoint is in this die.
        if(bad==2)m.clear();
        if(bad==3)m[1]=259; // Beyond supported die range.
        bool rejected=false;
        try{RRBackend invalid(f.nodes,f.edges,f.dies,f.boxes,cfg,m,d);}catch(const std::invalid_argument&){rejected=true;}
        require(rejected,"inconsistent membership cannot be routed");
    }
    auto r=f.resources;bool rejected=false;
    try{backend.execute(f.nodes,f.edges,r,{{0,7,1,3,0,3,0,0,0}},{{{1,0,0}}},false);}
    catch(const std::invalid_argument&){rejected=true;}
    require(rejected && std::memcmp(r.data(),f.resources.data(),r.size()*sizeof(Resource))==0,
            "ambiguous terminal access must fail before mutation");
}
void native_membership_bounded_equivalence() {
    std::mt19937 rng(7142026);
    for(unsigned trial=0;trial<1000;++trial) {
        std::vector<std::uint16_t> masks(12),owners(12);
        for(auto& m:masks)m=1+rng()%7;
        masks[0]=1;masks[1]=3;masks[2]=6;masks[11]=4;
        for(unsigned n=0;n<12;++n) {
            std::vector<unsigned> ds;
            for(unsigned d=0;d<3;++d)if(masks[n]&(1U<<d))ds.push_back(d);
            owners[n]=ds[rng()%ds.size()];
        }
        std::vector<std::pair<unsigned,unsigned>> arcs{{0,1},{1,2},{2,11}};
        for(unsigned a=0;a<12;++a)for(unsigned b=1;b<12;++b)
            if(a!=b && (masks[a]&masks[b]) && rng()%4==0 &&
               std::find(arcs.begin(),arcs.end(),std::make_pair(a,b))==arcs.end())arcs.push_back({a,b});
        Fixture f(owners,arcs);std::vector<std::uint16_t> edge_dies;
        for(unsigned n=0;n<12;++n) {
            f.boxes[n]={static_cast<std::uint16_t>(rng()%15),0,15,0};
            for(unsigned i=0;i<f.nodes[n].edge_count;++i) {
                auto& e=f.edges[f.nodes[n].edge_begin+i];
                std::vector<unsigned> ds;
                for(unsigned d=0;d<3;++d)if(masks[n]&masks[e.dst]&(1U<<d))ds.push_back(d);
                edge_dies.push_back(ds[rng()%ds.size()]);e.base_cost_q=1+rng()%100;e.delay_q=rng()%200;
            }
        }
        RRBackendConfig full;full.downstream_cost=true;full.vpr_style_cost=trial%2;
        auto bounded=full;bounded.bound_downstream=true;
        RRBackend a(f.nodes,f.edges,f.dies,f.boxes,full,masks,edge_dies);
        RRBackend b(f.nodes,f.edges,f.dies,f.boxes,bounded,masks,edge_dies);
        std::vector<dieroute::WideCost> costs(12);
        for(auto& c:costs)c={std::uint64_t(256)<<(rng()%20),rng()%10000};
        auto ra=f.resources,rb=f.resources;
        const Task task{0,7,0,11,static_cast<std::uint16_t>(rng()%65536),30,0,0,0};
        auto pa=a.execute(f.nodes,f.edges,ra,{task},{{{0,0,0}}},true,&costs);
        auto pb=b.execute(f.nodes,f.edges,rb,{task},{{{0,0,0}}},true,&costs);
        require(pa.candidates[0].path==pb.candidates[0].path &&
                pa.candidates[0].attachment==pb.candidates[0].attachment &&
                pa.candidates[0].commit_status==pb.candidates[0].commit_status &&
                std::memcmp(ra.data(),rb.data(),ra.size()*sizeof(Resource))==0,
                "native membership bounded search differs from full local reverse search");
    }
}
int main(){try{
    native_membership_bounded_equivalence();native_membership_resource_identity();native_membership_tree_and_validation();multi_hop_sharing();repair_and_rollback();leave_and_reenter_die();source_root_filter();deterministic_capacity();downstream_delay_selection();shared_tree_reentry_comparison();bounded_downstream_equivalence();upstream_tree_delay();portal_seed_delay();multiplicative_cost_reference();criticality_changes_corridor_objective();
    std::cout<<"rr_backend_tb: PASS (multi-hop, sharing, aliases, repair, rollback, fallback, capacity)\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
