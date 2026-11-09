#include <boost/multiprecision/cpp_int.hpp>
#include <algorithm>
#include <cstdint>
#include <limits>
#include <queue>
#include <utility>
#include <vector>

using U = std::uint64_t;
using Big = boost::multiprecision::number<boost::multiprecision::cpp_int_backend<256,256,
    boost::multiprecision::unsigned_magnitude,boost::multiprecision::checked,void>>;
struct Word { U lo,hi; };
struct Result { U objective[4]; Word raw; U attach,count; };
static_assert(sizeof(Word)==16 && sizeof(Result)==64,"public limb ABI");
static Big big(Word x) { return Big(x.lo)+(Big(x.hi)<<64); }
static Word word(Big x) {
    if ((x>>128)!=0) throw std::overflow_error("raw exceeds 128 bits");
    const Big mask=std::numeric_limits<U>::max();
    return {static_cast<U>(x&mask),static_cast<U>((x>>64)&mask)};
}
struct Workspace {
    U n,epoch=0;
    std::vector<U> seen,visited,seed,priced,pn,pe;
    std::vector<Big> dist,seed_raw,price;
    using Item=std::pair<Big,U>;
    std::vector<Item> heap;
    explicit Workspace(U count):n(count),seen(n),visited(n),seed(n),priced(n),pn(n),pe(n),
        dist(n),seed_raw(n),price(n){}
};
extern "C" void* rc_criticality_create(U n) {
    try { return n?new Workspace(n):nullptr; } catch(...) { return nullptr; }
}
extern "C" void rc_criticality_destroy(void* p) { delete static_cast<Workspace*>(p); }

// Status 0: found, 1: unreachable, negative: invalid call/numeric/allocation.
// Never mutates the caller's retained tree or prices, including on rejection.
extern "C" int rc_criticality_expand(void* handle,U target,U p,U q,
    const U* row,const U* dest,const Word* increment,
    const U* seed_nodes,const Word* seed_arrival,U seed_count,
    const Word* base,const Word* prices,U* path,U path_capacity,Result* result,U* stats) {
    try {
        auto* w=static_cast<Workspace*>(handle);
        if(!w||target>=w->n||!q||p>q||!seed_count||!result||!stats||path_capacity<w->n) return -1;
        const U n=w->n;
        if (++w->epoch==0) {
            std::fill(w->seen.begin(),w->seen.end(),0);
            std::fill(w->visited.begin(),w->visited.end(),0);
            std::fill(w->seed.begin(),w->seed.end(),0);
            std::fill(w->priced.begin(),w->priced.end(),0);
            w->epoch=1;
        }
        const U e=w->epoch;std::fill(stats,stats+4,U(0));
        auto& heap=w->heap;heap.clear();std::greater<Workspace::Item> greater;
        for(U i=0;i<seed_count;++i) {
            U u=seed_nodes[i];if(u>=n||w->seed[u]==e)return -1;
            w->seed[u]=w->seen[u]=e;w->seed_raw[u]=big(seed_arrival[i]);
            w->dist[u]=Big(p)*w->seed_raw[u];heap.emplace_back(w->dist[u],u);++stats[2];
        }
        std::make_heap(heap.begin(),heap.end(),greater);
        bool found=false;
        while(!heap.empty()) {
            std::pop_heap(heap.begin(),heap.end(),greater);auto item=heap.back();heap.pop_back();
            U u=item.second;
            if(w->visited[u]==e||item.first!=w->dist[u])continue;
            w->visited[u]=e;++stats[0];
            if(u==target){found=true;break;}
            for(U slot=row[u];slot<row[u+1];++slot) {
                ++stats[1];U v=dest[slot];if(v>=n)return -1;
                if(w->seed[v]==e||w->visited[v]==e)continue;
                if(w->priced[v]!=e) {
                    w->price[v]=Big(q-p)*(big(base[v])+big(prices[v]));w->priced[v]=e;
                }
                Big next=item.first+Big(p)*big(increment[slot])+w->price[v];
                if(w->seen[v]!=e||next<w->dist[v]) {
                    w->seen[v]=e;w->dist[v]=next;w->pn[v]=u;w->pe[v]=slot;
                    heap.emplace_back(next,v);std::push_heap(heap.begin(),heap.end(),greater);++stats[2];
                }
            }
        }
        stats[3]=heap.capacity();
        if(!found)return 1;
        U u=target,count=0;Big extra=0;
        while(w->seed[u]!=e) {
            if(count>=n)return -1;
            U slot=w->pe[u];path[count++]=slot;extra+=big(increment[slot]);u=w->pn[u];
        }
        std::reverse(path,path+count);result->attach=u;result->count=count;
        result->raw=word(w->seed_raw[u]+extra);
        Big value=w->dist[target];const Big mask=std::numeric_limits<U>::max();
        for(unsigned i=0;i<4;++i) {result->objective[i]=static_cast<U>(value&mask);value>>=64;}
        return 0;
    } catch(const std::overflow_error&) {return -2;} catch(...) {return -3;}
}
