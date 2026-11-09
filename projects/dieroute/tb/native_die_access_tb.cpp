#include "native_die_access.hpp"
#include "native_corridor.hpp"
#include <iostream>
using namespace dieroute;
static void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
template<class F>void rejects(F f){bool yes=false;try{f();}catch(const std::exception&){yes=true;}check(yes,"expected worker rejection");}
static SparseSearchResult branch(uint32_t root,std::vector<uint32_t> path){SparseSearchResult r;r.status=SparseSearchStatus::found;r.attachment=root;r.path=path;r.hops=path.size();for(auto n:path){r.edges.push_back(root*100+n);root=n;}return r;}
int main(){try{
    const std::vector<uint32_t> masks{4,6,2,3,1,6,1,2,4};
    auto member=[&](uint32_t n){return masks.at(n);};auto layout=NativeOwnerLayout::from_membership(3,member);
    auto allowed=[](uint32_t n,uint32_t){return n<9;};auto edge=[](uint32_t a,uint32_t b,uint32_t p){return p==a*100+b;};
    NativeRouteState state(layout);state.start(7,0,allowed);state.start(8,8,allowed);
    struct Arc{uint32_t dst,die;};std::vector<std::vector<Arc>> graph(9);
    graph[0]={{1,2},{5,2}};graph[1]={{2,1}};graph[2]={{3,1}};graph[3]={{4,0}};
    auto expand=[&](uint32_t n,auto emit){for(auto a:graph[n])emit(a.dst,n*100+a.dst,a.die);};
    NativeCorridorRouter router({{1,6,6},{3,3,3},{5,6,6}},3,3,false,false,1,true,true);
    SparseSearch search;uint64_t expanded=0,visits=0;size_t labels=0;NativeDieAccess view(state,7,10);
    auto run=[&](auto cost,auto prepare){return router.run(state,7,4,0,9,search,{100,UINT64_MAX},expand,member,[](uint32_t){return true;},cost,prepare,[](uint32_t){return uint64_t(0);},[](uint32_t,uint32_t){return uint64_t(0);},expanded,visits,labels);};
    auto cost=[&](uint32_t n,uint32_t d){check(d!=UINT32_MAX,"unexpected host fallback");return view.cost(d,n,member(n));};
    auto result=run(cost,[](uint32_t,uint64_t){});
    check(result.path==std::vector<uint32_t>({1,2,3,4})&&result.cost==4&&result.hops==4&&view.validate(),"three-die worker route");
    check(search.worker_count()==3&&search.worker_metrics(0).labels==2&&search.worker_metrics(1).labels==3&&search.worker_metrics(2).labels==1,"labels stored on departure worker");
    check(search.worker_metrics(0).transfers==1&&search.worker_metrics(1).transfers==2&&search.worker_metrics(2).transfers==0,"boundary frontier messages");
    check(view.metrics(2).requests==2&&view.metrics(1).requests==1,"reverse-direction nonowner boundary reads");
    check(view.cost(2,1,6)==1&&view.metrics(2).cache_hits==1,"immutable demand cache reuse");
    rejects([&]{view.cost(2,4,1);});rejects([&]{view.cost(2,4,7);});
    // An off-path boundary request remains part of validation.
    state.accept(8,5,branch(8,{5}),allowed,edge);check(!view.validate(),"off-path boundary change escaped validation");
    state.ripup(8);check(!view.validate(),"empty-to-occupied-to-empty ABA escaped validation");
    NativeDieAccess owned(state,7,10);check(owned.cost(1,2,2)==1,"owned local read");
    state.accept(8,2,branch(8,{2}),allowed,edge);check(!owned.validate(),"owned read changed during candidate phase");state.ripup(8);
    NativeDieAccess checkpoint(state,7,10);auto copy=state;state.swap(copy);check(!checkpoint.validate(),"checkpoint replacement retained read generation");
    NativeDieAccess rejected(state,7,10);auto bad=branch(0,{1,4});bad.edges.back()=999;
    rejects([&]{state.accept(7,4,bad,allowed,edge);});check(rejected.validate(),"failed transaction changed read generation");
    NativeDieAccess current(state,7,10);result=run([&](uint32_t n,uint32_t d){return current.cost(d,n,member(n));},[](uint32_t,uint64_t){});
    check(current.validate(),"fresh retry invalid");state.accept(7,4,result,allowed,edge);
    NativeDieAccess shared(state,7,10);check(shared.cost(2,1,6)==1&&shared.validate(),"same-net sharing counted twice across boundary");
    // Failed preparation must not report a previous search's worker counters.
    state.ripup(7);rejects([&]{run(cost,[](uint32_t,uint64_t){throw std::overflow_error("prepare");});});
    for(const auto& m:router.trace().back().workers)check(m.expanded==0&&m.edge_visits==0,"stale work after prepare exception");
    NativeDieAccess overflow(state,7,10);unsigned evaluated=0;
    rejects([&]{run([&](uint32_t n,uint32_t d){if(++evaluated==3)throw std::overflow_error("worker cost");return overflow.cost(d,n,member(n));},[](uint32_t,uint64_t){});});
    uint64_t e=0,v=0;for(const auto& m:router.trace().back().workers){e+=m.expanded;v+=m.edge_visits;}
    check(e==router.trace().back().expanded&&v==router.trace().back().edge_visits&&e>0,"partial worker work lost on exception");
    std::cout<<"die-local label/queue ownership, remote boundary snapshots, off-path/owned/ABA validation, atomic failures and partial work passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
