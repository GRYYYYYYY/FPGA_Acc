#include "native_net_transaction.hpp"
#include <iostream>
using namespace dieroute;
static void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
template<class F>void rejects(F f){bool bad=false;try{f();}catch(const std::exception&){bad=true;}check(bad,"expected rejection");}
int main(){try{
    auto member=[](uint32_t n){return n==2||n==5?3U:n<2?1U:2U;};auto allowed=[](uint32_t,uint32_t){return true;};
    auto edge=[](uint32_t a,uint32_t b,uint32_t e){return a*10+b==e;};
    NativeRouteState state(NativeOwnerLayout::from_membership(2,member));state.start(0,0,allowed);state.start(1,1,allowed);
    NativeWorkerShadows cache;cache.reset(state.layout(),1);
    auto [absent,hit]=cache.query(state,1,5);check(!hit&&absent==NativeSummary{}&&cache.size()==1,"cold summary request");
    auto frames=cache.take_messages();check(frames.size()==2&&frames[0].kind()==1&&frames[1].kind()==2,"missing request/response");
    auto bytes=frames[1].encode();check(NativeSummaryPacket::decode(bytes.data()).words==frames[1].words&&bytes[0]==1&&bytes[8]==5&&bytes[13]==1&&bytes[14]==2,"summary wire layout");
    auto old=frames[1];SparseSearchResult branch;branch.status=SparseSearchStatus::found;branch.attachment=1;branch.path={5};branch.edges={15};branch.cost=1;branch.hops=1;state.accept(1,5,branch,allowed,edge);
    auto [stale,was_hit]=cache.query(state,1,5);check(was_hit&&stale.version==0,"cache silently refreshed");
    NativeNetProposal p;p.net=0;p.present=1;p.snapshot=std::make_shared<const NativeRouteState>(state);p.reads={5};p.shadow_reads.push_back({0,1,5,stale,true});
    auto validation=native_validate_net(state,p,1);check(validation.conflicts.empty()&&validation.stale_shadows.size()==1&&!validation.valid(),"stale off-path summary passed fresh-snapshot validation");
    auto revision=state.revision();check(!native_commit_net(state,p,1,allowed,edge)&&state.revision()==revision,"stale summary changed authority");
    p.overflow=true;check(!native_commit_net(state,p,1,allowed,edge),"stale overflow not replayable");
    auto updates=cache.refresh(state);check(updates.size()==1&&updates[0].kind()==3&&updates[0].value().occupancy==1,"subscribed publication missing");
    check(!cache.receive(old)&&cache.metrics.stale==1,"delayed message replaced newer version");
    check(!cache.receive(updates[0])&&cache.metrics.duplicates==1,"duplicate message applied twice");
    auto forged=updates[0];++forged.words[2];rejects([&]{cache.receive(forged);});
    auto current=cache.query(state,1,5).first;p.shadow_reads[0].seen=current;p.overflow=false;check(native_validate_net(state,p,1).valid(),"fresh summary invalidated");
    check(cache.refresh(state).empty(),"unchanged summary unnecessarily published");
    state.ripup(1);updates=cache.refresh(state);check(updates.size()==1&&updates[0].value().occupancy==0&&updates[0].value().version==2,"zero-occupancy tombstone omitted");
    cache.reset(state.layout(),2);check(!cache.receive(updates[0])&&cache.size()==0,"prior-session ABA admitted");
    rejects([&]{cache.reset(state.layout(),2);});rejects([&]{cache.query(state,0,5);});rejects([&]{cache.query(state,1,3);});
    forged=NativeSummaryPacket::make(2,1,5,1,1,3);rejects([&]{cache.receive(forged);});
    // Real reverse-die search consumes a warmed remote summary from owner die 0.
    NativeRouteState native(state.layout());native.start(0,3,allowed);native.start(1,4,allowed);
    NativeWorkerShadows persistent;persistent.reset(native.layout(),1);persistent.query(native,1,2);persistent.take_messages();
    branch.attachment=4;branch.path={2};branch.edges={42};native.accept(1,2,branch,allowed,edge);
    auto route=[&]{NativeCorridorRouter router({{2,3,3}},2,3,false,false,1,true,true);SparseSearch search;
        return native_propose_net(std::make_shared<const NativeRouteState>(native),0,{{0,0,0}},1,6,100,router,search,
            [](uint32_t n,auto offer){if(n==3)offer(2,32,1);if(n==2)offer(0,20,0);},member,allowed,edge,
            [](uint32_t,uint64_t){},[](uint32_t){return uint64_t(0);},[](uint32_t,uint32_t){return uint64_t(0);},true,&persistent);};
    auto initial=route();check(initial.branches[0].result.cost==2&&!native_validate_net(native,initial,1).valid(),"stale summary not used/validated");
    persistent.refresh(native);auto replay=route();check(replay.branches[0].result.cost==3&&native_commit_net(native,replay,1,allowed,edge),"fresh replay failed");
    auto tail=persistent.refresh(native);check(!tail.empty()&&tail[0].value().occupancy==2,"final publication tail omitted");
    std::cout<<"persistent summaries, fixed wire frames, delayed/duplicate/session rejection, off-path stale validation, tombstones and real stale-cost replay passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
