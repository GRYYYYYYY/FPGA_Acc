#include "native_monotone.hpp"
#include "sparse_search.hpp"
#include <functional>
#include <iostream>
#include <random>
using namespace dieroute;
static void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
struct Arc {std::uint32_t dst,die,key;};
int main(){try{
    NativeMonotonePolicy p({0,1,2},{0},9);
    check(p.edge(0,2,1,3,0)&&p.edge(2,4,3,2,1),"portal zero-hop transition");
    check(!p.edge(2,1,3,1,0)&&!p.edge(4,2,2,3,1),"no incidental boundary or backward transition");
    check(!p.edge(2,4,3,2,0),"physical PIP SLR matters");
    check(!p.edge(1,0,1,1,0),"no root reentry");
    NativeMonotonePolicy terminal({0,1},{0},2),local({1},{2},4);
    check(terminal.edge(0,2,1,3,0),"terminal boundary can cross with no outgoing PIP");
    check(local.edge(2,4,3,2,1),"shared boundary root can depart on destination die");
    check(!local.edge(4,3,2,3,1),"single-die path excludes incidental boundary");
    bool threw=false;try{NativeMonotonePolicy::check_boundary(7);}catch(const std::invalid_argument&){threw=true;}
    check(threw,"ambiguous multi-membership topology rejected explicitly");
    // Independent exhaustive physical-path oracle. It reasons about consecutive
    // PIP dies and the membership of the intervening electrical node; it never
    // calls the production entry/departure filter.
    std::mt19937 rng(20261014);SparseSearch search;unsigned reachable=0,unreachable=0;
    std::vector<std::uint32_t> masks={1,1,3,3,2,2,6,6,4,4};
    for(unsigned trial=0;trial<500;++trial){
        std::vector<std::vector<Arc>> g(10);std::vector<std::uint64_t> costs(10);
        for(auto& c:costs)c=1+rng()%7;
        for(unsigned src=0;src<10;++src)for(unsigned dst=0;dst<10;++dst)if(src!=dst)
            for(unsigned die=0;die<3;++die)if((masks[src]&masks[dst]&(1U<<die))&&rng()%5==0)
                g[src].push_back({dst,die,src*100+dst*3+die});
        if(trial%2==0){
            const std::uint32_t ns[]={0,1,2,4,6,8,9},ds[]={0,0,1,1,2,2};
            for(unsigned i=0;i<6;++i)g[ns[i]].push_back({ns[i+1],ds[i],10000+i});
        }
        std::uint64_t optimum=UINT64_MAX;std::uint32_t hops=UINT32_MAX;
        std::function<void(unsigned,unsigned,unsigned,std::uint64_t,unsigned)> dfs;
        dfs=[&](unsigned node,unsigned last_die,unsigned seen,std::uint64_t cost,unsigned depth){
            if(cost>optimum)return;
            if(node==9){if(last_die==2&&std::tie(cost,depth)<std::tie(optimum,hops)){optimum=cost;hops=depth;}return;}
            for(auto e:g[node]){
                if(seen&(1U<<e.dst))continue;
                if(node==0){if(e.die!=0)continue;}
                else if(masks[node]&(masks[node]-1)){if(e.die!=last_die+1)continue;}
                else if(e.die!=last_die)continue;
                dfs(e.dst,e.die,seen|(1U<<e.dst),cost+costs[e.dst],depth+1);
            }
        };
        dfs(0,0,1,0,0);
        auto result=search.run(10,{{0,0,0}},9,UINT32_MAX,[&](unsigned src,auto offer){
            for(auto e:g[src])if(p.edge(src,e.dst,masks[src],masks[e.dst],e.die))
                offer(e.dst,e.key,[&](){return std::optional<std::uint64_t>(costs[e.dst]);});
        });
        if(optimum==UINT64_MAX){++unreachable;check(result.status==SparseSearchStatus::exhausted,"oracle exhaustion");}
        else{++reachable;check(result.status==SparseSearchStatus::found&&result.cost==optimum&&result.hops==hops,"joint search agrees with exhaustive three-die physical-path oracle");}
    }
    check(reachable>250&&unreachable>0,"random oracle includes reachable and unreachable cases");
    std::cout<<"monotone physical edge policy and 500 exhaustive three-die graph comparisons passed: "<<reachable<<" reachable, "<<unreachable<<" unreachable\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
