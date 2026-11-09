#include "native_net_transaction.hpp"
#include <atomic>
#include <condition_variable>
#include <iostream>
#include <mutex>
using namespace dieroute;
static void check(bool yes,const char* why){if(!yes)throw std::runtime_error(why);}
template<class F>static void rejects(F f){bool rejected=false;try{f();}catch(const std::exception&){rejected=true;}check(rejected,"expected rejection");}
int main(){try{
    auto member=[](uint32_t n){return n==2?3U:n>=3?2U:1U;};
    auto allowed=[](uint32_t,uint32_t){return true;};
    auto edge=[](uint32_t a,uint32_t b,uint32_t key){return key==a*10+b;};
    NativeRouteState state(NativeOwnerLayout::from_membership(2,member));
    state.start(0,0,allowed);state.start(1,1,allowed);state.start(2,6,allowed);
    auto snapshot=std::make_shared<const NativeRouteState>(state);
    auto proposal=[&](uint32_t net,uint32_t source,uint32_t sink){
        NativeNetProposal p;p.net=net;p.present=1;p.snapshot=snapshot;p.reads={sink};
        SparseSearchResult branch;branch.status=SparseSearchStatus::found;branch.attachment=source;branch.path={sink};branch.edges={source*10+sink};branch.hops=1;branch.cost=1;
        p.branches.push_back({{net,sink,member(sink)==1?0U:1U},0,false,false,branch});return p;
    };
    auto first=proposal(0,0,2),second=proposal(1,1,2),disjoint=proposal(2,6,7);
    check(native_commit_net(state,first,1,allowed,edge),"first proposal commit");
    const auto before=state.revision();
    check(!native_commit_net(state,second,1,allowed,edge)&&state.revision()==before,"stale proposal changed authority");
    check(native_validate_net(state,disjoint,1).valid(),"unrelated publication invalidated disjoint net");
    check(native_commit_net(state,disjoint,1,allowed,edge),"disjoint proposal failed");
    // Off-path absent reads protect both newly occupied and rip-up/version ABA.
    auto off=proposal(1,1,4);off.reads={2,4};
    check(!native_validate_net(state,off,1).valid(),"off-path absent read omitted");
    state.ripup(0);check(!native_validate_net(state,off,1).valid(),"rip-up ABA accepted");
    auto overflow=off;overflow.overflow=true;check(!native_commit_net(state,overflow,1,allowed,edge),"stale overflow must replay");
    overflow.snapshot=std::make_shared<const NativeRouteState>(state);rejects([&]{native_commit_net(state,overflow,1,allowed,edge);});
    rejects([&]{native_validate_net(state,first,2);});
    // All accepted branches are staged: malformed later PIP cannot leave a prefix.
    auto bad=proposal(1,1,3);bad.snapshot=std::make_shared<const NativeRouteState>(state);bad.reads={3,4};
    auto later=bad.branches[0];later.task.sink=4;later.result.attachment=3;later.result.path={4};later.result.edges={999};later.result.hops=2;bad.branches.push_back(later);
    auto revision=state.revision();rejects([&]{native_commit_net(state,bad,1,allowed,edge);});
    check(state.revision()==revision&&state.tree(1).nodes.size()==1&&!state.find_use(3),"partial net publication");
    auto missing=bad;missing.branches.pop_back();missing.reads.clear();rejects([&]{native_commit_net(state,missing,1,allowed,edge);});
    // Same-net seed/tree changes invalidate even disjoint read footprints.
    auto same=proposal(2,6,8);same.reads={8};check(native_validate_net(state,same,1).tree_changed,"tree growth not validated");
    // Force both std::async executions to rendezvous; neither can complete alone.
    // The installed TSan misreports timed steady-clock condition waits; the
    // independently reproduced system-clock wait retains the same rendezvous.
    std::mutex mutex;std::condition_variable ready;unsigned arrived=0;std::atomic<unsigned> live{0},peak{0};
    auto results=native_parallel_propose({0,1},[&](size_t,uint32_t net){
        auto active=++live;auto old=peak.load();while(active>old&&!peak.compare_exchange_weak(old,active)){}
        {std::unique_lock<std::mutex> lock(mutex);++arrived;ready.notify_all();check(ready.wait_until(lock,std::chrono::system_clock::now()+std::chrono::seconds(5),[&]{return arrived==2;}),"parallel jobs did not overlap");}
        --live;NativeNetProposal p;p.net=net;return p;
    });
    check(peak==2&&results[0].net==0&&results[1].net==1,"nonparallel execution/order");
    check(results[0].begin_ns<=results[1].end_ns&&results[1].begin_ns<=results[0].end_ns,"execution intervals do not overlap");
    rejects([&]{native_parallel_propose({0,0},[](size_t,uint32_t){return NativeNetProposal{};});});
    std::atomic<unsigned> finished{0};rejects([&]{native_parallel_propose({0,1},[&](size_t i,uint32_t){if(i==0)throw std::runtime_error("worker failed");++finished;return NativeNetProposal{};});});
    check(finished==1,"failed batch did not join remaining worker");
    // Exercise actual joint corridor + private multi-sink tree growth.
    NativeRouteState native(NativeOwnerLayout::from_membership(2,member));native.start(0,0,allowed);native.start(1,1,allowed);
    auto base=std::make_shared<const NativeRouteState>(native);
    auto route=[&](uint32_t net){
        NativeCorridorRouter router({{2,3,3}},2,3,false,false,1,true,true);SparseSearch search;
        std::vector<NativeNetTask> tasks{{net*2,3,1},{net*2+1,4,1}};
        return native_propose_net(base,net,tasks,1,9,100,router,search,
            [&](uint32_t n,auto offer){if(n<2)offer(2,n*10+2,0);if(n==2)offer(3,23,1);if(n==3)offer(4,34,1);},member,allowed,edge,
            [](uint32_t,uint64_t){},[](uint32_t){return uint64_t(0);},[](uint32_t,uint32_t){return uint64_t(0);});
    };
    auto batch=native_parallel_propose({0,1},[&](size_t,uint32_t n){return route(n);});
    check(batch[0].branches.size()==2&&batch[0].branches[1].result.attachment==3&&batch[0].branches[1].result.path==std::vector<uint32_t>{4},"private shared-tree growth lost");
    check(native_commit_net(native,batch[0],1,allowed,edge)&&!native_commit_net(native,batch[1],1,allowed,edge),"cross-net conflict missed");
    base=std::make_shared<const NativeRouteState>(native);auto replay=route(1);
    check(replay.branches[0].result.cost==4&&native_commit_net(native,replay,1,allowed,edge),"current-state replay incorrect");
    check(native.overused()==3&&native.use(2).version==2,"negotiated occupancy/version mismatch");
    NativeRouteState tiny(NativeOwnerLayout::from_membership(2,member));tiny.start(0,0,allowed);
    NativeCorridorRouter tiny_router({{2,3,3}},2,3,false,false,1,true,true);SparseSearch tiny_search;
    auto budget=native_propose_net(std::make_shared<const NativeRouteState>(tiny),0,{{0,3,1},{1,4,1}},1,9,1,tiny_router,tiny_search,
        [&](uint32_t n,auto offer){if(n==0)offer(2,2,0);if(n==2)offer(3,23,1);if(n==3)offer(4,34,1);},member,allowed,edge,
        [](uint32_t,uint64_t){},[](uint32_t){return uint64_t(0);},[](uint32_t,uint32_t){return uint64_t(0);});
    check(budget.passes.size()==2&&!budget.passes[0].rescue&&budget.passes[1].rescue&&!budget.passes[1].retry,"whole-net budget rescue failed to terminate");
    revision=tiny.revision();check(native_commit_net(tiny,budget,1,allowed,edge)&&tiny.revision()==revision&&tiny.tree(0).nodes.size()==1,"failed net proposal modified authority");
    std::cout<<"parallel whole-net search, disjoint acceptance, off-path/ABA/tree conflicts, current replay, stale overflow and atomic late-failure publication passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
