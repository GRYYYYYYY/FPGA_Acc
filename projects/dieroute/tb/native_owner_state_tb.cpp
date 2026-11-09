#include "native_route_state.hpp"
#include <iostream>
#include <random>
#include <sstream>
using namespace dieroute;
static void check(bool ok,const char* s){if(!ok)throw std::runtime_error(s);}
static auto allowed=[](uint32_t n,uint32_t){return n<100;};
static auto edge=[](uint32_t a,uint32_t b,uint32_t p){return p==a*100+b;};
static uint32_t membership(uint32_t n){return n==7?6:n==8?7:1u<<(n%3);}
static SparseSearchResult branch(uint32_t from,std::vector<uint32_t> path){
    SparseSearchResult b;b.status=SparseSearchStatus::found;b.attachment=from;b.hops=path.size();b.path=path;
    for(auto n:path){b.edges.push_back(from*100+n);from=n;}return b;
}
static std::string snapshot(const NativeRouteState& s){std::ostringstream out;
    s.visit_uses([&](auto n,const auto& u){out<<n<<':'<<u.history<<':'<<u.version;for(auto net:u.nets)out<<','<<net;out<<';';});
    for(const auto& [net,t]:s.trees()){out<<net<<'@'<<t.source;for(const auto& [n,v]:t.nodes)out<<';'<<n<<','<<v.parent<<','<<v.pip<<','<<v.depth;}return out.str();
}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}check(caught,"expected rejection");}
template<class F>void unchanged(NativeRouteState& s,F f){auto before=snapshot(s);reject(f);check(snapshot(s)==before,"partial cross-owner mutation");}
static void inventory(const NativeRouteState& s){size_t count=0;std::set<uint32_t> seen;
    for(uint32_t d=0;d<s.owner_count();++d)for(const auto& [n,u]:s.owner_uses(d)){
        check(seen.insert(n).second&&s.owner(n)==d,"duplicated or misplaced authority");
        check(s.owner_use(d,n)==&u&&s.find_use(n)==&u,"lookup uses another authority copy");++count;
        if(s.owner_count()>1)reject([&]{s.owner_use((d+1)%s.owner_count(),n);});
    }
    std::vector<uint32_t> sorted;s.visit_uses([&](auto n,const auto&){sorted.push_back(n);});
    check(std::is_sorted(sorted.begin(),sorted.end())&&count==s.use_count(),"canonical merge/count");
}
int main(){try{
    auto layout=NativeOwnerLayout::from_membership(3,membership);
    check(layout.owner(7)==1&&layout.owner(8)==0,"shared electrical node assigned wrong owner");
    reject([&]{NativeOwnerLayout::from_membership(0,membership);});
    reject([&]{NativeOwnerLayout::from_membership(9,membership);});
    for(auto mask:{0u,8u,256u})reject([&]{NativeOwnerLayout::from_membership(3,[=](uint32_t){return mask;}).owner(1);});
    NativeRouteState flat,split(layout);for(auto s:{&flat,&split})for(uint32_t net=1;net<=4;++net)s->start(net,90+net,allowed);
    std::mt19937 rng(7241);
    for(unsigned step=0;step<1000;++step){auto net=1+rng()%4;std::vector<uint32_t> path;std::set<uint32_t> used;
        for(unsigned i=0,k=1+rng()%8;i<k;++i){auto n=rng()%30;if(used.insert(n).second)path.push_back(n);}
        for(auto s:{&flat,&split}){s->ripup(net);s->accept(net,path.back(),branch(90+net,path),allowed,edge);}
        if(step%3==0)check(flat.negotiate(2)==split.negotiate(2),"partition negotiation mismatch");
        check(snapshot(flat)==snapshot(split)&&flat.overused()==split.overused(),"partition routing semantics changed");
        for(uint32_t n=0;n<30;++n)check(flat.cost(n,net,17)==split.cost(n,net,17),"partition cost mismatch");
        inventory(split);
    }
    auto restored=NativeRouteState::checkpoint(split.trees(),split.snapshot_uses(),allowed,edge,split.layout());
    check(snapshot(restored)==snapshot(split)&&restored.layout().same(layout),"checkpoint lost layout/state");inventory(restored);
    auto copy=split;copy.ripup(1);check(snapshot(split)==snapshot(flat),"copy aliases owner maps");
    restored.swap(flat);check(restored.owner_count()==1&&flat.owner_count()==3&&snapshot(flat)==snapshot(split),"swap split layout from authority");
    NativeRouteState late({{2,NativeUse{{},0,UINT64_MAX}}},layout);late.start(1,0,allowed);
    unchanged(late,[&]{late.accept(1,2,branch(0,{3,1,2}),allowed,edge);});inventory(late);
    NativeRouteState rip(layout);rip.start(1,0,allowed);rip.accept(1,2,branch(0,{3,1,2}),allowed,edge);
    auto uses=rip.snapshot_uses();uses.at(2).version=UINT64_MAX;
    rip=NativeRouteState::checkpoint(rip.trees(),uses,allowed,edge,layout);
    unchanged(rip,[&]{rip.ripup(1);});
    NativeRouteState history({{3,NativeUse{{1,2},0,0}},{1,NativeUse{{1,2},0,0}},{2,NativeUse{{1,2},UINT64_MAX-2,0}}},layout);
    unchanged(history,[&]{history.negotiate(2);});
    NativeRouteState version({{3,NativeUse{{1,2},0,0}},{2,NativeUse{{1,2},0,UINT64_MAX}}},layout);
    unchanged(version,[&]{version.negotiate(1);});check(version.negotiate(0).size()==2,"zero increment should not exhaust version");
    auto invalid=NativeOwnerLayout::from_membership(3,[](uint32_t n){return n==2?0:1u<<(n%3);});
    NativeRouteState rejected(invalid);rejected.start(1,0,allowed);
    unchanged(rejected,[&]{rejected.accept(1,2,branch(0,{3,1,2}),allowed,edge);});
    std::cout<<"1000 cross-owner transactions, unique storage, shared membership, checkpoint/copy/swap and late-owner rejection passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
