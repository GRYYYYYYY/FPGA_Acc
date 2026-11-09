#include "joint_state.hpp"

#include <iostream>
#include <limits>
#include <stdexcept>
#include <utility>

using namespace fusionpar::joint;
namespace {
unsigned checks=0;
void require(bool condition,const char* description) {
    ++checks;
    if(!condition) throw std::runtime_error(description);
}
// Two sinks on net 10 share node 2. Source can move from node 0 to 1;
// one sink can move from node 3 to 5. Node 6 is an unreachable legal site pin.
std::pair<Design,State> fixture() {
    Design d;
    d.nodes={{0,1,0},{1,1,0},{2,3,1},{5,0,0},{5,0,0},{5,0,0},{5,0,0}};
    d.edges={{2,1,1},{2,1,1},{3,1,1},{4,1,1},{5,1,1}};
    d.sites={{0,0,0,0,{{0,0,true}}},{1,0,0,0,{{0,1,true}}},
             {2,0,0,1,{{0,3,false}}},{3,0,0,1,{{0,4,false}}},
             {4,0,0,1,{{0,5,false}}},{5,0,0,1,{{0,6,false}}}};
    d.instances={{0,false,{0,1}},{1,false,{2,4,5}},{1,true,{3}}};
    d.connections={{10,0,0,1,0,32,0},{10,0,0,2,0,32,1}};
    State s; s.placement={{0,0},{2,0},{3,0}};s.site_versions.resize(6);
    s.routes={{0,3,{2,3},0},{0,4,{2,4},0}};
    s.resources.resize(7);for(auto& r:s.resources) r={0,1,256,0,0,invalid};
    s.criticalities={0,0};initialize_accounting(d,s);
    return {d,s};
}
Proposal source_move() {return {1,{{0,0,1,0}}};}
Proposal sink_move(Id site=4) {return {2,{{1,2,site,0}}};}
Router router() {persistroute::PathfinderConfig cfg;cfg.max_iterations=3;return pr_cmodel_router(cfg);}
void core() {
    auto [d,s]=fixture(); std::string detail;
    require(validate_state(d,s,detail),"fixture validity");
    require(s.resources[2].occupancy==1,"shared branch counted once per net");
    Engine e(d,s,router());
    auto before=semantic_digest(e.state());auto tx=e.prepare(source_move());
    require(tx.status()==Status::ready,"PR source move prepares");
    require(semantic_digest(e.state())==before,"prepare preserves state");
    require(tx.metrics().affected_connections==2,"whole net invalidation");
    require(tx.candidate()->routes[0].source==1 && tx.candidate()->routes[1].source==1,"all sink roots remapped");
    require(e.commit(tx)==Status::committed,"atomic publish");
    require(e.state().placement[0].site==1 && e.state().placement[0].version==1,"placement committed");
    require(e.state().site_versions[0]==1 && e.state().site_versions[1]==1,"site versions committed");
    require(e.state().resources[2].occupancy==1 && e.state().resources[2].version==1,"unique shared resource version bump");
    require(e.state().routes[0].version==1 && e.state().routes[1].version==1,"route versions bumped");
    require(validate_state(d,e.state(),detail),"committed state valid");
    auto committed=semantic_digest(e.state());
    require(e.commit(tx)==Status::consumed && semantic_digest(e.state())==committed,"double commit blocked");

    Engine sink(d,s,router());auto st=sink.prepare(sink_move());
    require(st.status()==Status::ready,"sink move prepares");
    require(st.candidate()->routes[0].sink==5 && st.candidate()->routes[1].sink==4,"sink endpoint remapping");
    require(st.candidate()->resources[3].occupancy==0 && st.candidate()->resources[5].occupancy==1,"old branch released/new branch reserved");
}
void aborts() {
    auto [d,s]=fixture();Engine e(d,s,router());auto digest=semantic_digest(e.state());
    auto fail=e.prepare(sink_move(5));require(fail.status()==Status::route_failed,"unreachable pin fails");
    require(e.commit(fail)==Status::route_failed && semantic_digest(e.state())==digest,"routing failure aborts all state");
    auto veto=e.prepare(source_move(),[](const auto&,const auto&,const auto&){return false;});
    require(veto.status()==Status::sketch_rejected && veto.metrics().expanded==0,"sketch skips routing");
    auto quality=e.prepare(source_move(),{},[](const auto&,const auto&,const auto&){return false;});
    require(quality.status()==Status::quality_rejected && semantic_digest(e.state())==digest,"quality veto aborts");
    Proposal stale=source_move();stale.moves[0].observed_version=99;
    require(e.prepare(stale).status()==Status::stale_state,"stale proposal detected");
    Proposal duplicate=source_move();duplicate.moves.push_back(duplicate.moves[0]);
    require(e.prepare(duplicate).status()==Status::invalid_move,"duplicate instance detected");
    require(e.prepare({3,{{2,3,4,0}}}).status()==Status::invalid_move,"fixed block detected");
    require(e.prepare({3,{{1,2,3,0}}}).status()==Status::placement_illegal,"occupied/forbidden site detected");
    auto tx=e.prepare(source_move());auto other=e.prepare(sink_move());
    require(e.commit(other)==Status::committed,"second candidate commits");
    auto next=semantic_digest(e.state());
    require(e.commit(tx)==Status::stale_state && semantic_digest(e.state())==next,"old snapshot cannot overwrite new state");

    Engine t(d,s,router());auto timing=t.prepare(source_move());
    t.timing_barrier(t.state().revision,{1,2});next=semantic_digest(t.state());
    require(t.commit(timing)==Status::stale_timing && semantic_digest(t.state())==next,"timing barrier abort");
    bool caught=false;try{t.timing_barrier(0,{3,4});}catch(const std::invalid_argument&){caught=true;}
    require(caught && semantic_digest(t.state())==next,"stale timing callback abort");
    Engine foreign(d,s,router());auto ft=foreign.prepare(source_move());
    require(t.commit(ft)==Status::foreign_transaction,"transaction engine identity");
    require(foreign.commit(ft)==Status::committed,"foreign attempt does not consume rightful transaction");
}
void malformed() {
    auto [d,s]=fixture();const auto real=router();
    Router bad=[&](const RoutingRequest& req){auto reply=real(req);reply.tasks[0].path={6,req.tasks[0].sink};return reply;};
    Engine e(d,s,bad);auto before=semantic_digest(e.state());auto tx=e.prepare(source_move());
    require(tx.status()==Status::candidate_invalid,"independent adjacency validator rejects backend");
    require(e.commit(tx)==Status::candidate_invalid && semantic_digest(e.state())==before,"malformed candidate preserves state");
    Router missing=[&](const RoutingRequest& req){auto reply=real(req);reply.tasks.pop_back();return reply;};
    Engine m(d,s,missing);require(m.prepare(source_move()).status()==Status::candidate_invalid,"missing route rejected");
    Router throwing=[](const RoutingRequest&)->RoutingReply{throw std::runtime_error("injected backend exception");};
    Engine x(d,s,throwing);require(x.prepare(source_move()).status()==Status::route_failed,"backend exception contained");
    unsigned calls=0;Validator native=[&](const auto&,const auto&,std::string& detail){++calls;detail="injected native rejection";return calls==1;};
    Engine n(d,s,real,native);require(n.prepare(source_move()).status()==Status::candidate_invalid,"native gate aborts");
    s.resources[2].version=std::numeric_limits<std::uint32_t>::max();
    Engine overflow(d,s,real);before=semantic_digest(overflow.state());
    require(overflow.prepare(source_move()).status()==Status::candidate_invalid && semantic_digest(overflow.state())==before,"version overflow fails closed");
    s.resources[2].occupancy=2;std::string error;
    require(!validate_state(d,s,error),"accounting corruption rejected");
    auto fresh=fixture();fresh.second.resources[2].history_cost_q=65535;
    Engine numeric(fresh.first,fresh.second,real);auto nt=numeric.prepare(source_move());
    require(nt.status()==Status::route_failed && nt.detail().find("numeric guard")!=std::string::npos,
            "saturated PR cost fails closed");
}
void repair_and_repeat() {
    auto [d,s]=fixture();std::string expected;
    for(unsigned repeat=0;repeat<5;++repeat) {
        Engine e(d,s,router());
        auto repair=[](const auto&,const auto&,const auto& failed,Status){return std::vector<Proposal>{failed,sink_move()};};
        auto result=run_proposal(e,sink_move(5),2,repair);
        require(result.accepted && result.attempts.size()==2,"bounded repair skips duplicate and succeeds");
        require(result.attempts[0].before==result.attempts[0].after,"failed repair state unchanged");
        auto hash=semantic_digest(e.state());
        if(repeat==0) expected=hash;else require(hash==expected,"five repeats semantic determinism");
    }
    Engine e(d,s,router());
    auto repeat_bad=[](const auto&,const auto&,const auto& failed,Status){return std::vector<Proposal>{failed};};
    auto exhausted=run_proposal(e,sink_move(5),100,repeat_bad);
    require(!exhausted.accepted && exhausted.attempts.size()==1,"duplicate repairs cannot oscillate");
    auto zero=run_proposal(e,sink_move(5),0,repeat_bad);
    require(zero.attempts.size()==1,"zero repair budget");
    auto proposals=propose_moves(d,s,20);require(!proposals.empty(),"deterministic proposal generator");
    for(const auto& p:proposals) for(const auto& m:p.moves) require(!d.instances[m.instance].fixed,"generator preserves fixed blocks");
}
void macros_and_swaps() {
    auto [d,s]=fixture();
    d.instances[1].allowed_sites={2,3,4,5};d.instances[2].allowed_sites={2,3,4,5};d.instances[2].fixed=false;
    Engine e(d,s,router());auto swap=e.prepare({4,{{1,2,3,0},{2,3,2,0}}});
    require(swap.status()==Status::ready && e.commit(swap)==Status::committed,"simultaneous swap legal");
    require(e.state().site_versions[2]==1 && e.state().site_versions[3]==1,"swap versions increment once");
    d.macros={{1,{{2,1,0,0}}}};
    Engine macro(d,s,router());
    require(macro.prepare(sink_move()).status()==Status::placement_illegal,"partial macro move rejected");
}
void global_repair() {
    Design d;
    d.nodes={{0,1,0},{1,1,0},{2,1,1},{3,0,0},{3,2,0},{5,0,0},{5,2,1},{7,1,1}};
    d.edges={{2,1,1},{6,1,1},{3,1,1},{6,1,1},{7,2,1},{3,1,1},{5,1,1},{5,1,1}};
    d.sites={{0,0,0,0,{{0,0,true}}},{1,0,0,0,{{0,1,true}}},
             {2,0,0,1,{{0,3,false}}},{3,0,0,2,{{0,4,true}}},{4,0,0,3,{{0,5,false}}}};
    d.instances={{0,false,{0,1}},{1,true,{2}},{2,true,{3}},{3,true,{4}}};
    d.connections={{10,0,0,1,0,32,0},{20,2,0,3,0,32,1}};
    State s;s.placement={{0,0},{2,0},{3,0},{4,0}};s.site_versions.resize(5);
    s.routes={{0,3,{2,3},0},{4,5,{6,5},0}};s.criticalities={0,0};
    s.resources.resize(8);for(auto& resource:s.resources)resource={0,1,256,0,0,invalid};
    initialize_accounting(d,s);Engine e(d,s,router());auto before=semantic_digest(e.state());
    auto local=e.prepare(source_move());require(local.status()==Status::route_failed,"local move cannot displace unaffected net");
    require(local.feedback().connection_ids==std::vector<Id>{0} && local.feedback().resource_ids==std::vector<Id>{6},"PR capacity failure identifies its connection and resource");
    require(semantic_digest(e.state())==before,"local congestion failure preserves both nets");
    auto global=e.prepare(source_move(),{}, {},true);
    require(global.status()==Status::ready,"global route repair releases conflicting net");
    persistroute::PathfinderConfig cfg;cfg.max_iterations=3;
    Engine control(d,s,retained_cmodel_router(cfg));auto paired=control.prepare(source_move(),{},{},true);
    require(paired.status()==Status::ready && semantic_digest(*paired.candidate())==semantic_digest(*global.candidate()),"FP tree controller reproduces congestion negotiation result");
    require(paired.metrics().route_iterations==global.metrics().route_iterations && paired.metrics().expanded==global.metrics().expanded,"FP tree controller matches repeated PR searches");
    require(global.metrics().affected_connections==2 && global.metrics().touched_resources==5,"global footprint recorded");
    require(e.commit(global)==Status::committed,"global repair atomic commit");
    require(e.state().routes[1].path==std::vector<Id>({7,5}),"unaffected blocker moved to alternate corridor");
}
void placement_repair() {
    auto [d,s]=fixture();Engine e(d,s,router());auto before=semantic_digest(e.state());
    const auto bad=sink_move(5);auto failed=e.prepare(bad);
    require(failed.status()==Status::route_failed && !failed.feedback().connection_ids.empty(),"unreachable sink has routing feedback");
    auto alternatives=propose_repairs(d,e.state(),bad,failed.status(),failed.feedback(),1);
    require(alternatives.size()==1,"placement repair obeys requested budget");
    require(alternatives[0].moves.size()==1 && alternatives[0].moves[0].instance==1 && alternatives[0].moves[0].new_site==4,
            "feedback targets the failed sink and contracts displacement");
    require(semantic_digest(e.state())==before,"repair generation is read-only");
    auto ready=e.prepare(alternatives[0]);require(ready.status()==Status::ready && e.commit(ready)==Status::committed,"routing failure repaired by a different legal placement");
    require(e.state().placement[0].site==0 && e.state().placement[1].site==4,"repair preserves uninvolved driver");
    require(propose_repairs(d,s,bad,Status::stale_state,failed.feedback(),1).empty(),"stale transaction is not a repair trigger");
    require(propose_repairs(d,s,bad,Status::route_failed,{},1).empty(),"missing evidence does not produce blind repair");
    require(propose_repairs(d,e.state(),bad,Status::route_failed,failed.feedback(),1).empty(),"repair requires original snapshot versions");
    auto malformed=failed.feedback();malformed.connection_ids={999};bool caught=false;
    try {propose_repairs(d,s,bad,Status::route_failed,malformed,1);}catch(const std::invalid_argument&){caught=true;}
    require(caught,"malformed repair witness fails closed");
    FailureFeedback native{FeedbackKind::native_delay,{0},{}};
    require(propose_repairs(d,s,bad,Status::quality_rejected,native,1).size()==1,"native quality rejection can drive placement repair");
}
void retained_branches() {
    auto [d,s]=fixture();persistroute::PathfinderConfig cfg;cfg.max_iterations=3;
    const auto backend=retained_cmodel_router(cfg);
    Engine e(d,s,backend);auto before=semantic_digest(e.state());
    auto tx=e.prepare(sink_move(),{},{},false,true);
    require(tx.status()==Status::ready,"retained branch prepares with real seeded kernel");
    require(tx.metrics().retained_connections==std::vector<Id>{1} && tx.metrics().kernel_searches==1,"unchanged sink eliminates one kernel search");
    require(tx.candidate()->routes[1].path==s.routes[1].path && tx.candidate()->routes[1].version==0,"retained path and version unchanged");
    require(tx.candidate()->resources[2].occupancy==1 && tx.candidate()->resources[3].occupancy==0,"retained shared prefix counted once and obsolete tail released");
    require(semantic_digest(e.state())==before && e.commit(tx)==Status::committed,"retention remains private until atomic commit");
    std::string detail;require(validate_state(d,e.state(),detail),"retained publication independently valid");
    Engine original(d,s,router()),control(d,s,backend),root(d,s,backend);
    auto a=original.prepare(source_move()),b=control.prepare(source_move()),c=root.prepare(source_move(),{},{},false,true);
    require(a.status()==Status::ready && b.status()==Status::ready && c.status()==Status::ready,"whole-tree controls prepare");
    require(semantic_digest(*a.candidate())==semantic_digest(*b.candidate()) && a.metrics().expanded==b.metrics().expanded,"empty retention reproduces PR tree and search effort");
    require(c.metrics().retained_connections.empty() && c.metrics().kernel_searches==2 && semantic_digest(*b.candidate())==semantic_digest(*c.candidate()),"source move invalidates all old branches");
    Engine failed(d,s,backend);auto bad=failed.prepare(sink_move(5),{},{},false,true);
    require(bad.status()==Status::route_failed && bad.feedback().connection_ids==std::vector<Id>{0},"retained tree failure reports changed connection");
    require(semantic_digest(failed.state())==before,"failed retained route cannot leak reservations");
    Router corrupt=[&](const RoutingRequest& request){auto result=backend(request);result.tasks[1].path={};return result;};
    Engine malformed(d,s,corrupt);
    require(malformed.prepare(sink_move(),{},{},false,true).status()==Status::candidate_invalid,"backend cannot silently replace a retained branch");
    require(control.prepare(sink_move(),{},{},true,true).status()==Status::invalid_move,"conflicting global-reroute and retain flags rejected");
    // Two nets share RR nodes at capacity 2. An occupancy-only retained adapter
    // would double-count these owners when constructing the dynamic trees.
    for(auto& site:d.sites){auto pin=site.terminals[0];pin.pin=1;site.terminals.push_back(pin);}
    d.connections.push_back({20,0,1,1,1,32,2});d.connections.push_back({20,0,1,2,1,32,3});
    s.routes.push_back(s.routes[0]);s.routes.push_back(s.routes[1]);s.criticalities.resize(4);
    for(auto& resource:s.resources)resource.capacity=2;initialize_accounting(d,s);
    Engine shared(d,s,backend);auto multi=shared.prepare(sink_move(),{},{},false,true);
    require(multi.status()==Status::ready && multi.metrics().retained_connections==std::vector<Id>({1,3}),"multiple retained nets supported at capacity >1");
    require(multi.candidate()->resources[2].occupancy==2 && multi.candidate()->resources[2].owner==invalid,"exact multi-owner retained accounting");
    require(shared.commit(multi)==Status::committed && validate_state(d,shared.state(),detail),"shared retained publication validates");
}
void fixed_placement_epoch() {
    auto [d,s]=fixture();Engine engine(d,s,router());auto before=semantic_digest(s);
    require(engine.prepare({}).status()==Status::invalid_move,"normal empty proposal still rejected");
    auto epoch=engine.prepare_routing();
    require(epoch.status()==Status::ready && epoch.metrics().affected_connections==2,"explicit fixed-placement epoch reroutes every connection");
    require(semantic_digest(engine.state())==before,"routing epoch remains private before commit");
    require(epoch.candidate()->placement[0].site==s.placement[0].site && epoch.candidate()->placement[0].version==0 && epoch.candidate()->site_versions==s.site_versions,"routing epoch preserves placement/site versions");
    require(epoch.candidate()->routes[0].version==1 && epoch.candidate()->routes[1].version==1,"routing epoch advances route versions");
    require(engine.commit(epoch)==Status::committed && engine.commit(epoch)==Status::consumed,"routing epoch publishes once");
    Engine veto(d,s,router());auto rejected=veto.prepare_routing([](const auto&,const auto&,const auto&){return false;});
    require(rejected.status()==Status::quality_rejected && semantic_digest(veto.state())==before,"routing epoch acceptance rejection preserves state");
    unsigned validations=0;Engine native(d,s,router(),[&](const auto&,const auto&,auto&){return ++validations==1;});
    require(native.prepare_routing().status()==Status::candidate_invalid && semantic_digest(native.state())==before,"routing epoch cannot bypass native validator");
}
void upstream_tree_timing() {
    // First sink establishes a slow prefix 0->1. The second sink can cheaply
    // attach there, or take the faster full path 0->4->3. Charging only newly
    // added edges prefers the slow prefix; charging upstream delay must not.
    Design d;d.nodes={{0,2,0},{2,2,1},{4,0,0},{4,0,0},{4,1,1}};
    d.edges={{1,1,1000},{4,1,10},{2,1,1},{3,1,1},{3,1,10}};
    std::vector<persistroute::Resource> resources(5,{0,1,256,0,0,invalid});
    std::vector<persistroute::Task> tasks={{0,10,0,2,0,32,0,0,0},{1,10,0,3,65535,32,1,0,0}};
    std::vector<persistroute::RoutedTask> retained={{tasks[0],{1,2},true}};
    for(std::uint16_t weight: {0,256}) {
        persistroute::PathfinderConfig cfg;cfg.max_iterations=3;cfg.route_tree_timing_weight_q=weight;
        auto pr=pr_cmodel_router(cfg)({d,resources,tasks});
        auto empty=retained_cmodel_router(cfg)({d,resources,tasks});
        auto reuse=retained_cmodel_router(cfg)({d,resources,tasks,&retained});
        require(pr.success && empty.success && reuse.success,"weighted PR and retained controllers route legally");
        const std::vector<Id> expected=weight?std::vector<Id>{4,3}:std::vector<Id>{1,3};
        require(pr.tasks[1].path==expected && empty.tasks[1].path==expected && reuse.tasks[1].path==expected,
                "upstream delay weight changes attachment in all controllers");
        require(pr.expanded==empty.expanded && pr.kernel_searches==empty.kernel_searches,
                "weighted empty-tree control preserves PR search semantics");
        require(reuse.tasks[0].path==retained[0].path && reuse.kernel_searches==1,
                "weighted routing preserves retained branch without searching it");
    }
}
}
int main() {
    try {core();aborts();malformed();repair_and_repeat();macros_and_swaps();global_repair();placement_repair();retained_branches();fixed_placement_epoch();upstream_tree_timing();
        std::cout<<"fusionpar_joint_tb: PASS ("<<checks<<" checks, real PR HBM C-model)\n";return 0;}
    catch(const std::exception& e){std::cerr<<"FAIL after "<<checks<<" checks: "<<e.what()<<'\n';return 1;}
}
