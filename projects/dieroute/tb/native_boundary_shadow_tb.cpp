#include "native_boundary_shadow.hpp"
#include <iostream>
using namespace dieroute;
static void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
static auto allowed=[](uint32_t n,uint32_t){return n<20;};
static auto edge=[](uint32_t a,uint32_t b,uint32_t key){return key==a*100+b;};
static auto member=[](uint32_t n){return n==1?3U:2U;};
static SparseSearchResult branch(uint32_t root,std::vector<uint32_t> path){
    SparseSearchResult r;r.status=SparseSearchStatus::found;r.attachment=root;r.hops=path.size();r.path=path;
    for(auto n:path){r.edges.push_back(root*100+n);root=n;}return r;
}
template<class F>static void fails(F f){bool failed=false;try{f();}catch(const std::exception&){failed=true;}check(failed,"expected failure");}
int main(){try{
    NativeRouteState s;s.start(7,0,allowed);s.start(8,9,allowed);
    NativeBoundaryShadows shadows(2);fails([&]{shadows.view(1,7,1);});shadows.publish(s,member);
    auto zero=shadows.view(1,7,10);check(zero.cost(s,1,3)==1&&zero.reads()==1&&zero.valid(s),"implicit unused boundary summary");
    s.accept(8,1,branch(9,{1}),allowed,edge);check(!zero.valid(s),"absent-to-occupied read must invalidate");
    shadows.publish(s,member);auto stale=shadows.view(1,7,10);
    auto owner=shadows.view(0,7,10);check(owner.cost(s,1,3)==11&&owner.reads()==0,"owner uses authority");
    auto shared=shadows.view(1,8,10);check(shared.cost(s,1,3)==1&&shared.reads()==0,"same-net tree does not pay occupancy twice");
    s.ripup(8);
    SparseSearch search;std::vector<std::vector<uint32_t>> adj(10);
    adj[0]={1,2};adj[1]={4};adj[2]={3};adj[3]={4};
    auto run=[&](auto cost){return search.run(10,s.seeds(7),4,100,[&](uint32_t n,auto offer){
        for(auto dst:adj[n])offer(dst,n*100+dst,[&](){return std::optional<uint64_t>(cost(dst));});});};
    auto result=run([&](uint32_t n){return stale.cost(s,n,member(n));});
    check(result.path==std::vector<uint32_t>({2,3,4}),"stale occupied alternative yields detour");
    check(stale.reads()==1&&!stale.valid(s),"OFF-PATH decision read must invalidate candidate");
    check(s.tree(7).nodes.size()==1&&s.use(1).nets.empty(),"speculative search never mutates authority");
    auto current=run([&](uint32_t n){return s.cost(n,7,10);});
    check(current.path==std::vector<uint32_t>({1,4}),"fresh replay recovers cheaper path");
    // Publication must not silently refresh an already-created immutable view.
    shadows.publish(s,member);check(stale.cost(s,1,3)==11&&!stale.valid(s),"old view remains stale after publication");
    auto tombstone=shadows.view(1,7,10);check(tombstone.cost(s,1,3)==1&&tombstone.valid(s)&&shadows.records()==1,"empty ownership retains version");
    s.accept(8,1,branch(9,{1}),allowed,edge);s.ripup(8);
    check(!tombstone.valid(s),"same occupancy ABA rejected by version");
    shadows.publish(s,member);auto oldEpoch=shadows.view(1,7,10);oldEpoch.cost(s,1,3);
    shadows.invalidate();shadows.publish(s,member);check(!oldEpoch.valid(s),"checkpoint epoch invalidates equal resource versions");
    // Stale overflow is replayable; genuine current overflow remains an error.
    s.accept(8,1,branch(9,{1}),allowed,edge);shadows.publish(s,member);
    auto overflow=shadows.view(1,7,UINT64_MAX);fails([&]{overflow.cost(s,1,3);});check(overflow.valid(s),"current overflow validates but cannot commit");
    s.ripup(8);fails([&]{overflow.cost(s,1,3);});check(!overflow.valid(s)&&s.cost(1,7,UINT64_MAX)==1,"stale overflow must replay");
    fails([&]{shadows.view(2,7,1);});fails([&]{owner.cost(s,1,0);});fails([&]{owner.cost(s,1,4);});
    // A malformed checkpoint cannot reset versions through publication.
    NativeRouteState empty;empty.start(7,0,allowed);fails([&]{shadows.publish(empty,member);});
    shadows.invalidate();shadows.publish(empty,member);check(shadows.records()==0,"explicit epoch reset permits fresh checkpoint");
    check(shadows.metrics().logical_deliveries==shadows.metrics().changed_summaries,"two dies deliver each changed summary to one nonowner");
    std::cout<<"native boundary off-path validation, immutable snapshots, same-net sharing, ABA, epoch and overflow passed\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
