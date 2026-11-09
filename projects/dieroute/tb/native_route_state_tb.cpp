#include "native_route_state.hpp"
#include <iostream>
#include <sstream>
using namespace dieroute;
static void check(bool ok,const char* what){if(!ok)throw std::runtime_error(what);}
static auto allowed=[](uint32_t n,uint32_t){return n<100;};
static auto edge=[](uint32_t a,uint32_t b,uint32_t key){return key==a*100+b;};
static SparseSearchResult branch(uint32_t attachment,uint32_t depth,std::vector<uint32_t> path){
    SparseSearchResult r;r.status=SparseSearchStatus::found;r.attachment=attachment;r.hops=depth+path.size();r.path=path;
    for(auto n:path){r.edges.push_back(attachment*100+n);attachment=n;}return r;
}
static std::string snapshot(const NativeRouteState& s){std::ostringstream out;
    for(const auto& [n,u]:s.snapshot_uses()){out<<n<<':'<<u.history<<':'<<u.version;for(auto net:u.nets)out<<','<<net;out<<';';}
    for(const auto& [net,t]:s.trees()){out<<net<<'@'<<t.source;for(const auto& [n,v]:t.nodes)out<<';'<<n<<','<<v.parent<<','<<v.pip<<','<<v.depth;}return out.str();}
template<class F>static void rejects_unchanged(NativeRouteState& s,F f){auto before=snapshot(s);bool rejected=false;try{f();}catch(const std::exception&){rejected=true;}check(rejected&&snapshot(s)==before,"rejection must leave authority/tree unchanged");}
int main(){try{
    NativeRouteState state;state.start(7,0,allowed);state.start(8,9,allowed);
    state.accept(7,3,branch(0,0,{1,2,3}),allowed,edge);
    state.accept(7,4,branch(2,2,{4}),allowed,edge);
    check(state.use(2).nets.size()==1&&state.use(2).version==1,"shared prefix counted once");
    check(state.path(7,4)==std::vector<std::pair<uint32_t,uint32_t>>({{1,1},{2,102},{4,204}}),"complete prefix/PIP path");
    auto snap=snapshot(state);state.accept(7,2,branch(2,2,{}),allowed,edge);check(snapshot(state)==snap,"existing sink is no-op");
    state.accept(8,5,branch(9,0,{2,5}),allowed,edge);check(state.overused()==1,"inter-net electrical conflict");
    check(state.cost(2,6,4)==9&&state.cost(2,7,4)==5,"projected distinct-net congestion");
    check(state.negotiate(3)==std::set<uint32_t>({7,8})&&state.use(2).history==3,"all conflicting nets pending");
    auto oldVersion=state.use(2).version;state.ripup(7);check(state.use(2).nets==std::set<uint32_t>({8})&&state.use(2).version==oldVersion+1&&state.use(2).history==3,"ripup keeps other net/history");
    check(state.tree(7).nodes.size()==1&&state.use(0).nets.count(7),"source reservation survives ripup");
    state.accept(7,6,branch(0,0,{1,6}),allowed,edge);check(state.overused()==0,"rerouted net removes conflict");
    rejects_unchanged(state,[&]{state.accept(7,6,branch(1,1,{6}),allowed,edge);});
    auto bad=branch(1,1,{10,11});bad.edges.back()=99;rejects_unchanged(state,[&]{state.accept(7,11,bad,allowed,edge);});
    auto denied=[](uint32_t n,uint32_t){return n!=11;};rejects_unchanged(state,[&]{state.accept(7,11,branch(1,1,{10,11}),denied,edge);});
    bad=branch(1,1,{10,11});bad.hops=999;rejects_unchanged(state,[&]{state.accept(7,11,bad,allowed,edge);});
    NativeRouteState overflow({{3,NativeUse{{},0,UINT64_MAX}}});overflow.start(1,0,allowed);
    rejects_unchanged(overflow,[&]{overflow.accept(1,3,branch(0,0,{1,2,3}),allowed,edge);});
    NativeRouteState history({{4,NativeUse{{1,2},UINT64_MAX-2,0}},{5,NativeUse{{1,2},0,0}}});
    rejects_unchanged(history,[&]{history.negotiate(2);});
    bool costOverflow=false;try{history.cost(4,9,2);}catch(const std::overflow_error&){costOverflow=true;}check(costOverflow,"cost overflow fails closed");
    // Closed-loop negotiated routing: net 1 initially takes the resource net 2
    // needs, then moves to its longer alternate after history/present updates.
    NativeRouteState loop;loop.start(1,0,allowed);loop.start(2,4,allowed);SparseSearch search;
    std::vector<std::vector<uint32_t>> adjacency(9);adjacency[0]={1,2};adjacency[1]={5,6};adjacency[2]={3};adjacency[3]={7};adjacency[7]={5};adjacency[4]={1};
    std::set<uint32_t> pending{1,2};bool legal=false;uint64_t present=1;
    for(unsigned epoch=0;epoch<8;++epoch){if(epoch)for(auto net:pending)loop.ripup(net);
        for(auto net:pending){uint32_t sink=net==1?5:6;auto r=search.run(9,loop.seeds(net),sink,100,[&](uint32_t n,auto offer){for(auto dst:adjacency[n])offer(dst,n*100+dst,[&](){return std::optional<uint64_t>(loop.cost(dst,net,present));});});
            check(r.status==SparseSearchStatus::found,"fixture route reachable");loop.accept(net,sink,r,allowed,edge);}
        if(!loop.overused()){legal=true;break;}pending=loop.negotiate(1);present*=2;
    }
    check(legal&&loop.tree(1).nodes.count(2)&&!loop.tree(1).nodes.count(1)&&loop.tree(2).nodes.count(1),"negotiated loop repairs shared resource");
    std::cout<<"native shared-tree ownership, atomic rejection, ripup, overflow and negotiated-loop tests passed\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
