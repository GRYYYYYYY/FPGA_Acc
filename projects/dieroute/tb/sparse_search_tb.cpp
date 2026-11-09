#include "sparse_search.hpp"
#include <iostream>
#include <queue>
#include <random>
#include <set>
#include <unordered_map>
using namespace dieroute;
static void require(bool ok,const char* what){if(!ok)throw std::runtime_error(what);}
struct Arc{uint32_t dst,key;uint64_t cost;bool allowed;};
using Graph=std::vector<std::vector<Arc>>;
// Frozen dense label algorithm used before the sparse conversion. Keep its
// storage and relaxation independent from the new table/heap implementation.
static SparseSearchResult dense(const Graph& graph,const std::vector<SparseSeed>& seeds,uint32_t sink,uint32_t max_hops){
    const auto count=graph.size();std::vector<uint64_t> dist(count,UINT64_MAX);
    std::vector<uint32_t> hops(count,UINT32_MAX),parent(count,UINT32_MAX),edges(count,UINT32_MAX);
    std::vector<bool> root(count),closed(count);
    using Entry=std::tuple<uint64_t,uint32_t,uint32_t,uint32_t>;
    std::priority_queue<Entry,std::vector<Entry>,std::greater<Entry>> queue;SparseSearchResult out;
    for(auto s:seeds)if(s.hops<=max_hops && std::tie(s.cost,s.hops)<std::tie(dist[s.node],hops[s.node])){
        dist[s.node]=s.cost;hops[s.node]=s.hops;root[s.node]=true;queue.emplace(s.cost,s.hops,s.node,UINT32_MAX);}
    while(!queue.empty()){
        const auto [cost,depth,n,p]=queue.top();queue.pop();(void)p;
        if(closed[n]||cost!=dist[n]||depth!=hops[n])continue;
        closed[n]=true;++out.expanded;
        if(n==sink){out.status=SparseSearchStatus::found;out.cost=cost;out.hops=depth;auto at=n;
            while(parent[at]!=UINT32_MAX){out.path.push_back(at);out.edges.push_back(edges[at]);at=parent[at];}
            out.attachment=at;std::reverse(out.path.begin(),out.path.end());std::reverse(out.edges.begin(),out.edges.end());return out;}
        if(depth>=max_hops)continue;
        for(auto edge:graph[n]){
            ++out.edge_visits;if(closed[edge.dst]||root[edge.dst]||!edge.allowed)continue;
            const auto next=cost+edge.cost;const auto nhops=depth+1;
            if(std::tie(next,nhops,n,edge.key)<std::tie(dist[edge.dst],hops[edge.dst],parent[edge.dst],edges[edge.dst])){
                dist[edge.dst]=next;hops[edge.dst]=nhops;parent[edge.dst]=n;edges[edge.dst]=edge.key;queue.emplace(next,nhops,edge.dst,n);}
        }
    }return out;
}
static void tables(){
    SparseNodeTable<uint64_t,uint8_t> table(UINT64_MAX);std::mt19937 random(81267);
    std::size_t largest=0;
    for(unsigned epoch=0;epoch<600;++epoch){table.reset();std::unordered_map<uint32_t,uint64_t> expected;
        for(unsigned k=0;k<1000;++k){auto n=random();auto value=uint64_t(random())<<32|random();table.touch(n)=value;expected[n]=value;
            if(k%3==0)table.touch(n)=expected[n]=value+1;}
        for(auto [key,value]:expected)require(table.contains(key)&&table.get(key)==value,"hash/epoch lookup");
        require(table.size()==expected.size(),"duplicate insertion");largest=std::max(largest,table.retained_bytes());
    }
    require(largest<100000,"table storage proportional to touched set");
    table.reset();require(table.size()==0&&table.get(0)==UINT64_MAX,"reset absent default");
    table.touch(UINT32_MAX)=4;require(table.get(UINT32_MAX)==4,"full u32 key space");
}
static void differential(){
    std::mt19937 random(20261013);SparseSearch sparse;
    for(unsigned trial=0;trial<3000;++trial){
        Graph graph(24);uint32_t key=0;
        for(uint32_t a=0;a<24;++a)for(uint32_t b=0;b<24;++b)if(random()%7==0)
            for(unsigned p=0;p<1+random()%2;++p)graph[a].push_back({b,key++,random()%5,(random()%5)!=0});
        std::vector<SparseSeed> seeds{{0,0,0},{3,static_cast<uint32_t>(random()%3),random()%13},{3,0,random()%9}};
        auto budget=trial%3?30U:5U;
        auto expected=dense(graph,seeds,23,budget);uint64_t expanded=0,visits=0;
        auto actual=sparse.run(graph.size(),seeds,23,budget,[&](uint32_t n,auto offer){
            for(auto edge:graph[n])offer(edge.dst,edge.key,[&]()->std::optional<uint64_t>{if(!edge.allowed)return {};return edge.cost;});
        },{},&expanded,&visits);
        SparseSearch distributed;std::array<uint64_t,3> worker_visits{};
        auto sharded=distributed.run_guided_partitioned(graph.size(),seeds,23,budget,3,[](uint32_t n){return n%3;},[&](uint32_t n,auto offer){
            for(auto e:graph[n]){++worker_visits[n%3];offer(e.dst,e.key,[&]()->std::optional<uint64_t>{if(!e.allowed)return {};return e.cost;});}
        },[](uint32_t){return uint64_t(0);});
        require(sharded.status==actual.status&&sharded.path==actual.path&&sharded.edges==actual.edges&&sharded.attachment==actual.attachment&&sharded.hops==actual.hops&&sharded.cost==actual.cost&&sharded.expanded==actual.expanded&&sharded.edge_visits==actual.edge_visits,"sharded queue changes single-queue order");
        uint64_t worker_expanded=0,worker_labels=0;
        for(uint32_t d=0;d<3;++d){auto m=distributed.worker_metrics(d);worker_expanded+=m.expanded;worker_labels+=m.labels;
            require(m.edge_visits==worker_visits[d]&&m.transfers<=m.pushes,"worker work attribution");}
        require(worker_expanded==actual.expanded&&worker_labels==distributed.touched(),"worker sums disagree");
        require((actual.status==SparseSearchStatus::found)==(expected.status==SparseSearchStatus::found),"dense found mismatch");
        require(actual.path==expected.path&&actual.edges==expected.edges&&actual.attachment==expected.attachment&&actual.hops==expected.hops&&actual.cost==expected.cost,"dense path/cost tie mismatch");
        require(actual.expanded==expected.expanded&&actual.edge_visits==expected.edge_visits&&expanded==actual.expanded&&visits==actual.edge_visits,"dense metrics mismatch");
    }
}
static void boundaries(){
    SparseSearch search;
    auto expand=[](uint32_t n,auto offer){if(n<4)offer(n+1,n,[](){return std::optional<uint64_t>(1);});};
    for(unsigned repeat=0;repeat<10;++repeat){
        auto result=search.run(91975782,{{0,0,0}},4,10,expand);
        require(result.status==SparseSearchStatus::found&&result.path==std::vector<uint32_t>({1,2,3,4}),"huge sparse ID range");
        require(search.touched()==5&&search.retained_bytes()<4096,"no full-graph label allocation");
    }
    require(search.run(8,{{0,0,0}},4,10,expand,{2,UINT64_MAX}).status==SparseSearchStatus::budget_exhausted,"label limit is not unreachable");
    require(search.run(8,{{0,0,0}},4,10,expand,{100,1}).status==SparseSearchStatus::budget_exhausted,"expansion limit is not unreachable");
    require(search.run(8,{{0,0,0}},4,1,expand).status==SparseSearchStatus::hop_limited,"hop cutoff explicit");
    require(search.run(8,{{0,0,0}},7,10,expand).status==SparseSearchStatus::exhausted,"exhausted graph");
    uint64_t expanded=0,visits=0;bool overflow=false;
    try{search.run(8,{{0,0,0}},4,10,[](uint32_t,auto offer){offer(1,0,[](){return std::optional<uint64_t>(UINT64_MAX);});},{},&expanded,&visits);}
    catch(const std::overflow_error&){overflow=true;}
    require(overflow&&expanded==1&&visits==1,"overflow retains work accounting");
    require(search.run(8,{{0,0,0}},4,10,expand).status==SparseSearchStatus::found,"reuse after exception");
    for(size_t labels:{size_t(1),size_t(2),size_t(5)})for(uint64_t expansions:{0ULL,1ULL,8ULL})for(uint64_t cost:{2ULL,8ULL}){
        SparseSearchLimits limits{labels,expansions,cost};auto flat=search.run(8,{{0,0,0}},4,10,expand,limits);
        auto part=search.run_guided_partitioned(8,{{0,0,0}},4,10,3,[](uint32_t n){return n%3;},expand,[](uint32_t){return uint64_t(0);},limits);
        require(part.status==flat.status&&part.path==flat.path&&part.expanded==flat.expanded&&part.edge_visits==flat.edge_visits,"partitioned budgets must remain global");
        uint64_t touched=0;for(uint32_t d=0;d<3;++d)touched+=search.worker_metrics(d).labels;
        require(touched==search.touched()&&touched<=labels,"global partition label limit");
    }
    auto zero=search.run(8,{{4,7,13}},4,10,expand);require(zero.path.empty()&&zero.cost==13&&zero.hops==7,"zero-hop root");
}
static void guided(){
    std::mt19937 random(18291);SparseSearch search;
    for(unsigned trial=0;trial<1500;++trial){
        Graph graph(24);uint32_t key=0;std::vector<uint64_t> h(12,UINT64_MAX);h[11]=0;
        for(uint32_t from=0;from<24;++from)for(uint32_t to=0;to<24;++to)if(random()%10==0)
            graph[from].push_back({to,key++,random()%17,random()%5!=0});
        // Bellman-Ford on a twelve-group relaxation (including forbidden arcs).
        for(unsigned pass=0;pass<12;++pass)for(uint32_t from=0;from<24;++from)for(auto e:graph[from])
            if(h[e.dst/2]!=UINT64_MAX)h[from/2]=std::min(h[from/2],e.cost+h[e.dst/2]);
        std::vector<uint64_t> optimum(24,UINT64_MAX);optimum[0]=0;
        for(unsigned pass=0;pass<24;++pass)for(uint32_t from=0;from<24;++from)for(auto e:graph[from])
            if(e.allowed && optimum[from]!=UINT64_MAX)optimum[e.dst]=std::min(optimum[e.dst],optimum[from]+e.cost);
        auto result=search.run_guided(24,{{0,0,0}},23,100,[&](uint32_t n,auto offer){
            for(auto e:graph[n])offer(e.dst,e.key,[&]()->std::optional<uint64_t>{if(!e.allowed)return {};return e.cost;});
        },[&](uint32_t n){return h[n/2];});
        auto partitioned=search.run_guided_partitioned(24,{{0,0,0}},23,100,3,[](uint32_t n){return n%3;},[&](uint32_t n,auto offer){
            for(auto e:graph[n])offer(e.dst,e.key,[&]()->std::optional<uint64_t>{if(!e.allowed)return {};return e.cost;});
        },[&](uint32_t n){return h[n/2];});
        require(partitioned.status==result.status&&partitioned.cost==result.cost&&partitioned.path==result.path&&partitioned.edges==result.edges&&partitioned.expanded==result.expanded&&partitioned.edge_visits==result.edge_visits,"partitioned A-star order differs from reference");
        require((result.status==SparseSearchStatus::found)==(optimum[23]!=UINT64_MAX),"guided reachability vs Bellman-Ford");
        if(result.status==SparseSearchStatus::found)require(result.cost==optimum[23],"guided optimal cost vs Bellman-Ford");
        std::vector<uint64_t> ceilings{0,9};
        if(optimum[23]!=UINT64_MAX){ceilings.push_back(optimum[23]);if(optimum[23])ceilings.push_back(optimum[23]-1);}
        for(auto ceiling:ceilings){
            auto bounded=search.run_guided(24,{{0,0,0}},23,100,[&](uint32_t n,auto offer){
                for(auto e:graph[n])offer(e.dst,e.key,[&]()->std::optional<uint64_t>{if(!e.allowed)return {};return e.cost;});
            },[&](uint32_t n){return h[n/2];},{100,UINT64_MAX,ceiling});
            const bool feasible=optimum[23]!=UINT64_MAX&&optimum[23]<=ceiling;
            require((bounded.status==SparseSearchStatus::found)==feasible,"cost ceiling vs independent Bellman-Ford optimum");
            if(feasible)require(bounded.cost==result.cost&&bounded.path==result.path&&bounded.edges==result.edges,"inclusive ceiling preserves equal-cost path/ties");
        }
    }
    bool rejected=false;try{search.run_guided(3,{{0,0,0}},2,10,[](uint32_t,auto){},[](uint32_t){return uint64_t(1);});}
    catch(const std::invalid_argument&){rejected=true;}require(rejected,"nonzero sink potential rejected");
    require(search.run(3,{{2,0,13}},2,10,[](uint32_t,auto){},{100,UINT64_MAX,12}).status==SparseSearchStatus::cost_limited,"cost cutoff is not unreachable");
    require(search.run(3,{{2,0,13}},2,10,[](uint32_t,auto){},{100,UINT64_MAX,13}).status==SparseSearchStatus::found,"equal-cost seed remains eligible");
}
int main(){try{tables();differential();boundaries();guided();std::cout<<"sparse reset/wrap, 3000 dense comparisons, 1500 guided Bellman-Ford comparisons and limit cases passed\n";return 0;}
catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
