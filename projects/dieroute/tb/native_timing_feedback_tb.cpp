#include "native_timing_feedback.hpp"
#include <iostream>
using namespace dieroute;
static void check(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
static auto allowed=[](uint32_t n,uint32_t){return n<100;};
static auto edge=[](uint32_t a,uint32_t b,uint32_t key){return key==a*100+b;};
static NativeRouteState state(bool proposal,NativeOwnerLayout layout){
    NativeRouteState s(layout);
    for(uint32_t net=1;net<=3;++net){auto src=net*10;s.start(net,src,allowed);
        // Baseline net 1 owns 1; proposal net 2 owns 1 and net 3 owns 2.
        // Restoring net 1 therefore requires the entire three-net closure.
        uint32_t middle=proposal?(net==1?4:net-1):net;
        SparseSearchResult b;b.status=SparseSearchStatus::found;b.attachment=src;b.hops=2;
        b.path={middle,src+1};b.edges={src*100+middle,middle*100+src+1};
        s.accept(net,src+1,b,allowed,edge);
    }
    return s;
}
static std::string exact(const NativeRouteState& s){std::ostringstream out;out<<native_tree_identity(s);
    for(const auto& [n,u]:s.snapshot_uses()){out<<n<<' '<<u.history<<' '<<u.version;for(auto net:u.nets)out<<' '<<net;out<<'\n';}return out.str();}
static NativeTimingSnapshot timing(const NativeRouteState& s,uint64_t epoch){
    NativeTimingSnapshot t;t.context="fixture context";t.trees=native_tree_identity(s);t.epoch=epoch;
    for(uint32_t net=1;net<=3;++net)for(auto kind:{NativeTimingKind::setup,NativeTimingKind::hold})
        t.loads.emplace(NativeTimingKey{net,net,kind},NativeTimingValue{NativeTimingCoverage::finite,kind==NativeTimingKind::setup?1434:29});
    return t;
}
template<class F> static void throws(F action){bool rejected=false;try{action();}catch(const std::exception&){rejected=true;}check(rejected,"expected rejection");}
int main(){try{
    for(bool partitioned:{false,true}){
    auto layout=partitioned?NativeOwnerLayout::from_membership(3,[](uint32_t n){return 1u<<(n%3);}):NativeOwnerLayout{};
    auto baseline=state(false,layout),proposal=state(true,layout);auto old=timing(baseline,0),now=timing(proposal,1);
    NativeTimingPolicy policy{0,20,false};NativeTimingController ctl(baseline,old,policy);
    auto before=exact(ctl.authority());now.loads.at({1,1,NativeTimingKind::hold}).slack_ps=4;
    auto d=ctl.consider(proposal,now);
    check(!d.selected_scope_accepted&&d.hold_violations==1&&d.setup_violations==0&&d.violating_nets==std::set<uint32_t>{1},"hold gate");
    check(exact(ctl.authority())==before&&ctl.epoch()==0,"hold rejection changed authority");
    auto repaired=restore_native_timing_nets(baseline,proposal,d.violating_nets,allowed,edge);
    check(repaired.restored_nets==std::set<uint32_t>({1,2,3})&&repaired.requires_native_timing,"repair conflict closure");
    check(native_tree_identity(repaired.candidate)==native_tree_identity(baseline),"closure did not restore baseline trees");
    check(exact(baseline)==before&&native_tree_identity(proposal)!=native_tree_identity(baseline),"repair changed source snapshots");
    throws([&]{ctl.consider(repaired.candidate,now);});check(exact(ctl.authority())==before,"stale proposal timing accepted");
    auto fresh=timing(repaired.candidate,1);check(ctl.consider(repaired.candidate,fresh).selected_scope_accepted&&ctl.epoch()==1,"fresh repair acceptance");
    auto accepted=exact(ctl.authority());throws([&]{ctl.consider(repaired.candidate,fresh);});check(exact(ctl.authority())==accepted,"replayed epoch changed authority");
    NativeTimingController setup(baseline,old,{1434,0,false});auto setupNow=timing(proposal,1);
    setupNow.loads.at({2,2,NativeTimingKind::setup}).slack_ps=1433;
    d=setup.consider(proposal,setupNow);check(!d.selected_scope_accepted&&d.setup_violations==1&&d.hold_violations==0,"setup gate");
    check(exact(setup.authority())==before,"setup rejection changed authority");
    NativeTimingController zero(baseline,old,{0,0,false});check(zero.consider(proposal,now).selected_scope_accepted,"positive small hold remains feasible at zero floor");
    NativeTimingController invalid(baseline,old,policy);
    auto reject=[&](NativeTimingSnapshot bad){throws([&]{invalid.consider(proposal,bad);});check(exact(invalid.authority())==before&&invalid.epoch()==0,"invalid oracle changed authority");};
    auto bad=timing(proposal,1);bad.context="different constraints";reject(bad);
    bad=timing(proposal,0);reject(bad);
    bad=timing(proposal,2);reject(bad);
    bad=timing(proposal,1);bad.loads.erase({1,1,NativeTimingKind::hold});reject(bad);
    bad=timing(proposal,1);bad.loads.at({1,1,NativeTimingKind::hold})={NativeTimingCoverage::unconstrained,{}};reject(bad);
    bad=timing(proposal,1);bad.loads.at({1,1,NativeTimingKind::hold})={NativeTimingCoverage::missing,{}};reject(bad);
    bad=timing(proposal,1);bad.loads.at({1,1,NativeTimingKind::hold}).slack_ps.reset();reject(bad);
    bad=timing(proposal,1);bad.loads.at({1,1,NativeTimingKind::hold}).coverage=NativeTimingCoverage::unconstrained;reject(bad);
    auto unconstrained=old;unconstrained.loads.at({3,3,NativeTimingKind::setup})={NativeTimingCoverage::unconstrained,{}};
    throws([&]{NativeTimingController fail(baseline,unconstrained,policy);});
    NativeTimingController explicitUnconstrained(baseline,unconstrained,{0,0,true});
    auto next=timing(proposal,1);next.loads.at({3,3,NativeTimingKind::setup})={NativeTimingCoverage::unconstrained,{}};
    d=explicitUnconstrained.consider(proposal,next);check(d.selected_scope_accepted&&d.unconstrained==1,"explicit stable unconstrained classification");
    auto missing=unconstrained;missing.loads.at({3,3,NativeTimingKind::setup}).coverage=NativeTimingCoverage::missing;
    throws([&]{NativeTimingController fail(baseline,missing,{0,0,true});});
    throws([&]{NativeTimingController fail(baseline,old,{0,30,false});});
    throws([&]{NativeTimingController fail(baseline,old,{-1,0,false});});
    auto exhausted=old;exhausted.epoch=UINT64_MAX;NativeTimingController maxEpoch(baseline,exhausted,policy);
    throws([&]{maxEpoch.consider(proposal,timing(proposal,0));});check(exact(maxEpoch.authority())==before,"epoch overflow changed authority");
    auto imported=NativeRouteState::checkpoint(baseline.trees(),baseline.snapshot_uses(),allowed,edge,layout);check(exact(imported)==before,"checkpoint did not preserve state");
    auto trees=baseline.trees();trees.at(1).nodes.at(1).depth=999;
    throws([&]{NativeRouteState::checkpoint(trees,baseline.snapshot_uses(),allowed,edge);});
    auto uses=baseline.snapshot_uses();uses.at(1).nets.clear();throws([&]{NativeRouteState::checkpoint(baseline.trees(),uses,allowed,edge);});
    uses=proposal.snapshot_uses();uses.at(4).version=UINT64_MAX;
    auto overflow=NativeRouteState::checkpoint(proposal.trees(),uses,allowed,edge,layout);auto overflowBefore=exact(overflow);
    throws([&]{restore_native_timing_nets(baseline,overflow,{1},allowed,edge);});check(exact(overflow)==overflowBefore,"repair overflow changed input");
    auto forbidden=[](uint32_t n,uint32_t){return n!=2;};
    throws([&]{restore_native_timing_nets(baseline,proposal,{1},forbidden,edge);});
    check(exact(baseline)==before,"repair failure changed baseline");
    check(ctl.authority().layout().same(layout)&&repaired.candidate.layout().same(layout),"repair/controller flattened partition layout");
    if(partitioned){auto flat=NativeRouteState::checkpoint(proposal.trees(),proposal.snapshot_uses(),allowed,edge);
        throws([&]{invalid.consider(flat,timing(flat,1));});check(exact(invalid.authority())==before,"layout change mutated authority");}
    }
    std::cout<<"native timing setup/hold, exact binding, atomic publication, coverage and conflict-closure repair passed\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
