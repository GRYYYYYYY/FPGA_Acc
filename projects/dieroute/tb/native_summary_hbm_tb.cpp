#include "native_net_transaction.hpp"
#include "native_summary_hbm.hpp"
#include <iostream>
#include <future>
using namespace dieroute;
static void check(bool x,const char* why){if(!x)throw std::runtime_error(why);}
int main(){try{for(bool push:{false,true}){
    auto member=[](uint32_t n){return n==2||n==5?3U:n<2?1U:2U;};auto allowed=[](uint32_t,uint32_t){return true;};auto edge=[](uint32_t a,uint32_t b,uint32_t e){return a*10+b==e;};
    auto layout=NativeOwnerLayout::from_membership(2,member);NativeRouteState state(layout);state.start(0,3,allowed);state.start(1,4,allowed);
    NativeSummaryHbm fabric(layout,{2,5},2,push);fabric.reset(1);fabric.publish(state);NativeHbmShadows cache(fabric,0);cache.reset(layout,1);
    check(!cache.query(state,1,2).second,"cold HBM lookup");cache.take_messages();
    SparseSearchResult branch;branch.status=SparseSearchStatus::found;branch.attachment=4;branch.path={2};branch.edges={42};branch.cost=1;branch.hops=1;state.accept(1,2,branch,allowed,edge);fabric.publish(state);
    auto route=[&]{NativeCorridorRouter router({{2,3,3}},2,3,false,false,1,true,true);SparseSearch search;
        return native_propose_net(std::make_shared<const NativeRouteState>(state),0,{{0,0,0}},1,6,100,router,search,
            [](uint32_t n,auto offer){if(n==3)offer(2,32,1);if(n==2)offer(0,20,0);},member,allowed,edge,
            [](uint32_t,uint64_t){},[](uint32_t){return uint64_t(0);},[](uint32_t,uint32_t){return uint64_t(0);},true,&cache);};
    auto p=route();auto stale=fabric.validate(0,p.shadow_reads);check(p.branches[0].result.cost==2&&!stale.empty()&&stale==native_validate_net(state,p,1).stale_shadows,"actual HBM stale cost/validation");
    auto revision=state.revision();check(!native_commit_net(state,p,1,allowed,edge)&&state.revision()==revision,"stale HBM candidate mutated authority");
    cache.refresh(state);p=route();check(p.branches[0].result.cost==3&&fabric.validate(0,p.shadow_reads).empty()&&native_commit_net(state,p,1,allowed,edge),"HBM fresh replay/commit");
    fabric.publish(state);cache.refresh(state);unsigned entries=0;fabric.inventory([&](auto,auto n,auto v){check(v==NativeWorkerShadows::authority(state,n),"owner mirror final state");},[&](auto,auto,auto n,auto v){check(v==NativeWorkerShadows::authority(state,n),"cache final state");++entries;});check(entries==1,"subscription inventory");
    check(push?cache.metrics.scans==0:cache.metrics.scans>0,"push path polled subscriptions");
    fabric.subscriptions([](auto,auto n,auto bits,auto pending,auto queued){check(bits==(n==2?UINT64_C(1)<<8:0)&&!pending&&!queued,"final publisher subscription state");});
    auto messages=fabric.take_frames(0);check(!messages.empty(),"missing endpoint command trace");fabric.take_frames(fabric.controller());fabric.reset(2);fabric.publish(state);cache.reset(layout,2);check(!cache.query(state,1,2).second,"new epoch reused subscription");
    // Two independent proposal lanes concurrently access the same owner CU
    // and distinct receiver records. Exercise shared serialization under TSan.
    NativeHbmShadows second(fabric,1);second.reset(layout,2);
    auto query=[&](NativeHbmShadows& worker){
        for(unsigned i=0;i<256;++i){auto n=i%2?2U:5U;
            check(worker.query(state,1,n).first==NativeWorkerShadows::authority(state,n),"concurrent endpoint value");}
        worker.take_messages();
    };
    auto first=std::async(std::launch::async,[&]{query(cache);});
    auto other=std::async(std::launch::async,[&]{query(second);});first.get();other.get();
    entries=0;fabric.inventory([](auto,auto,auto){},[&](auto,auto,auto n,auto value){check(value==NativeWorkerShadows::authority(state,n),"concurrent final cache");++entries;});
    check(entries==4,"concurrent lanes aliased receiver records");
    std::cout<<"live HBM mode="<<(push?2:1)<<" cost, owner validation, atomic rejection, refresh/replay and final inventories passed\n";
}
    // More than one output-ring worth of updates, with separate lanes and
    // repeated owner changes before delivery, exercises the host drain loop.
    auto layout=NativeOwnerLayout::from_membership(2,[](uint32_t n){return n<32?3U:1U;});NativeRouteState state(layout);
    std::vector<uint32_t> nodes;for(unsigned i=0;i<32;++i)nodes.push_back(i);
    for(auto n:nodes)state.start(n,32+n,[](auto,auto){return true;});
    NativeSummaryHbm fabric(layout,nodes,2,true);fabric.reset(1);fabric.publish(state);
    NativeHbmShadows a(fabric,0),b(fabric,1);a.reset(layout,1);b.reset(layout,1);
    for(auto n:nodes){a.query(state,1,n);b.query(state,1,n);}a.take_messages();b.take_messages();
    for(auto n:nodes){SparseSearchResult path;path.status=SparseSearchStatus::found;path.attachment=32+n;path.path={n};path.edges={n};path.hops=1;state.accept(n,n,path,[](auto,auto){return true;},[](auto,auto,auto){return true;});}
    fabric.publish(state);for(auto n:nodes)state.ripup(n);fabric.publish(state);
    for(auto* c:{&a,&b}){auto p=c->refresh(state);check(p.size()==32&&c->metrics.scans==0,"multiple-batch push drain");for(unsigned i=0;i<p.size();++i)check(p[i].node()==i&&p[i].value()==NativeWorkerShadows::authority(state,i),"coalesced sorted live updates");}
    fabric.subscriptions([](auto,auto,auto bits,auto pending,auto queued){check(bits==((UINT64_C(1)<<8)|(UINT64_C(1)<<9))&&!pending&&!queued,"multilane drain left pending state");});
    std::cout<<"live publisher multi-batch, coalescing and independent-lane drain passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
