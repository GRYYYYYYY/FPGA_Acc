#include <stdexcept>
#include <algorithm>
#include <cstdint>
#include <limits>
#include <queue>
#include <utility>
#include <vector>

using U = std::uint64_t;
struct Word { U lo,hi; };
struct Big {
    U v[4]={0,0,0,0};
    Big(U value=0) { v[0]=value; }
    bool operator==(const Big& b) const {
        for(unsigned i=0;i<4;++i) if(v[i]!=b.v[i])return false;
        return true;
    }
    bool operator!=(const Big& b) const { return !(*this==b); }
    bool operator<(const Big& b) const {
        for(int i=3;i>=0;--i)if(v[i]!=b.v[i])return v[i]<b.v[i];
        return false;
    }
    Big operator+(const Big& b) const {
        Big out;U carry=0;
        for(unsigned i=0;i<4;++i) {
            unsigned __int128 sum=static_cast<unsigned __int128>(v[i])+b.v[i]+carry;
            out.v[i]=U(sum);carry=U(sum>>64);
        }
        if(carry)throw std::overflow_error("256-bit addition");
        return out;
    }
    Big& operator+=(const Big& b) { *this=*this+b;return *this; }
};
static Big multiply(const Big& a,U factor) {
    Big out;U carry=0;
    for(unsigned i=0;i<4;++i) {
        unsigned __int128 value=static_cast<unsigned __int128>(a.v[i])*factor+carry;
        out.v[i]=U(value);carry=U(value>>64);
    }
    if(carry)throw std::overflow_error("256-bit multiplication");
    return out;
}
struct Result { U objective[4]; Word raw; U attach,count; };
static_assert(sizeof(Word)==16 && sizeof(Result)==64 && sizeof(Big)==32,"public limb ABI");
static Big big(Word x) { Big out;out.v[0]=x.lo;out.v[1]=x.hi;return out; }
static Word word(const Big& x) {
    if(x.v[2]||x.v[3])throw std::overflow_error("raw exceeds 128 bits");
    return {x.v[0],x.v[1]};
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
            w->dist[u]=multiply(w->seed_raw[u],p);heap.emplace_back(w->dist[u],u);++stats[2];
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
                    w->price[v]=multiply(big(base[v])+big(prices[v]),q-p);w->priced[v]=e;
                }
                Big next=item.first+multiply(big(increment[slot]),p)+w->price[v];
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
        for(unsigned i=0;i<4;++i)result->objective[i]=w->dist[target].v[i];
        return 0;
    } catch(const std::overflow_error&) {return -2;} catch(...) {return -3;}
}
