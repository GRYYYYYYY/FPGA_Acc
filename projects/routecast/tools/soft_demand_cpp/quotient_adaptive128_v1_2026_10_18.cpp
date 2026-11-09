#include "criticality_tree_exact_v2.cpp"
#include <tuple>

// Only the independent fast workspace uses these two limbs. The included
// legacy four-limb implementation and its exported symbols are unchanged.
struct Small128 {
 U v[2]={0,0};
 Small128(U value=0){v[0]=value;}
 bool operator==(const Small128& b)const{return v[0]==b.v[0]&&v[1]==b.v[1];}
 bool operator!=(const Small128& b)const{return !(*this==b);}
 bool operator<(const Small128& b)const{return v[1]!=b.v[1]?v[1]<b.v[1]:v[0]<b.v[0];}
 Small128 operator+(const Small128& b)const{
  Small128 out;U carry=0;
  for(unsigned i=0;i<2;++i){unsigned __int128 x=static_cast<unsigned __int128>(v[i])+b.v[i]+carry;out.v[i]=U(x);carry=U(x>>64);}
  if(carry)throw std::overflow_error("128bit add");return out;
 }
 Small128& operator+=(const Small128& b){*this=*this+b;return *this;}
};
static Small128 multiply128(const Small128& a,U factor){
 Small128 out;U carry=0;
 for(unsigned i=0;i<2;++i){unsigned __int128 x=static_cast<unsigned __int128>(a.v[i])*factor+carry;out.v[i]=U(x);carry=U(x>>64);}
 if(carry)throw std::overflow_error("128bit multiply");return out;
}
static Small128 big128(Word x){Small128 out;out.v[0]=x.lo;out.v[1]=x.hi;return out;}
static Word word128(const Small128& x){return {x.v[0],x.v[1]};}
struct Workspace128 {
 U n,epoch=0;
 std::vector<U> seen,visited,seed,priced,pn,pe;
 std::vector<Small128> dist,seed_raw,price;
 explicit Workspace128(U count):n(count),seen(n),visited(n),seed(n),priced(n),pn(n),pe(n),dist(n),seed_raw(n),price(n){}
};
static_assert(sizeof(Small128)==16,"fast limb width");

struct AWorkspace128: Workspace128 {
    U groups;
    std::vector<U> hseen;
    std::vector<Small128> hcache;
    using AItem=std::tuple<Small128,Small128,U>; // f, actual g, original node ID.
    std::vector<AItem> aheap;
    AWorkspace128(U n,U m):Workspace128(n),groups(m),hseen(m),hcache(m){}
};
static Small128 quad128(const U* values,U group) {
    if(values[4*group+2]||values[4*group+3])throw std::overflow_error("potential exceeds128 bits");
    Small128 out;
    for(unsigned i=0;i<2;++i)out.v[i]=values[4*group+i];
    return out;
}
static Small128 checked_key128(const Small128& cost,const Small128& h) {
    Small128 out=cost+h;
    return out;
}
extern "C" void* rc_quotient128_create(U n,U m) {
    try {return n&&m?new AWorkspace128(n,m):nullptr;}catch(...){return nullptr;}
}
extern "C" void rc_quotient128_destroy(void* handle) {delete static_cast<AWorkspace128*>(handle);}
extern "C" int rc_quotient128_expand(void* handle,U target,U p,U q,
    const U* row,const U* dest,const Word* increment,
    const U* seed_nodes,const Word* seed_arrival,U seed_count,
    const Word* base,const Word* prices,U* path,U path_capacity,Result* result,U* stats,
    const U* groups,const U* raw_h,const U* floor_h,const U* reachable) {
    try {
        auto* w=static_cast<AWorkspace128*>(handle);
        if(!w||target>=w->n||!q||p>q||!seed_count||!result||!stats||path_capacity<w->n)return -1;
        const U n=w->n;
        if(++w->epoch==0) {
            for(auto* a:{&w->seen,&w->visited,&w->seed,&w->priced,&w->hseen})std::fill(a->begin(),a->end(),0);
            w->epoch=1;
        }
        const U epoch=w->epoch;
        auto group_of=[&](U node){U group=groups[node];if(group>=w->groups)throw std::invalid_argument("group");return group;};
        auto heuristic=[&](U node)->const Small128& {
            U group=group_of(node);
            if(w->hseen[group]!=epoch) {
                w->hcache[group]=(p?multiply128(quad128(raw_h,group),p):Small128(0))+(q-p?multiply128(quad128(floor_h,group),q-p):Small128(0));
                w->hseen[group]=epoch;
            }
            return w->hcache[group];
        };
        std::fill(stats,stats+4,U(0));
        auto& heap=w->aheap;heap.clear();std::greater<AWorkspace128::AItem> greater;
        for(U i=0;i<seed_count;++i) {
            U u=seed_nodes[i];if(u>=n||w->seed[u]==epoch)return -1;
            w->seed[u]=w->seen[u]=epoch;w->seed_raw[u]=big128(seed_arrival[i]);
            if(!reachable[group_of(u)])continue;
            w->dist[u]=multiply128(w->seed_raw[u],p);
            heap.emplace_back(checked_key128(w->dist[u],heuristic(u)),w->dist[u],u);++stats[2];
        }
        std::make_heap(heap.begin(),heap.end(),greater);
        bool found=false;
        while(!heap.empty()) {
            std::pop_heap(heap.begin(),heap.end(),greater);auto item=heap.back();heap.pop_back();
            U u=std::get<2>(item);const Small128& cost=std::get<1>(item);
            if(w->visited[u]==epoch||cost!=w->dist[u])continue;
            w->visited[u]=epoch;++stats[0];
            if(u==target){found=true;break;}
            for(U slot=row[u];slot<row[u+1];++slot) {
                ++stats[1];U v=dest[slot];if(v>=n)return -1;
                if(w->seed[v]==epoch||w->visited[v]==epoch||!reachable[group_of(v)])continue;
                if(w->priced[v]!=epoch) {
                    w->price[v]=(q-p)?multiply128(big128(base[v])+big128(prices[v]),q-p):Small128(0);w->priced[v]=epoch;
                }
                Small128 next=cost+multiply128(big128(increment[slot]),p)+w->price[v];
                if(w->seen[v]!=epoch||next<w->dist[v]) {
                    w->seen[v]=epoch;w->dist[v]=next;w->pn[v]=u;w->pe[v]=slot;
                    heap.emplace_back(checked_key128(next,heuristic(v)),next,v);
                    std::push_heap(heap.begin(),heap.end(),greater);++stats[2];
                }
            }
        }
        stats[3]=heap.capacity();if(!found)return 1;
        U u=target,count=0;Small128 extra=0;
        while(w->seed[u]!=epoch) {
            if(count>=n)return -1;
            U slot=w->pe[u];path[count++]=slot;extra+=big128(increment[slot]);u=w->pn[u];
        }
        std::reverse(path,path+count);result->attach=u;result->count=count;
        result->raw=word128(w->seed_raw[u]+extra);
        for(unsigned i=0;i<2;++i)result->objective[i]=w->dist[target].v[i];
        result->objective[2]=result->objective[3]=0;
        return 0;
    }catch(const std::overflow_error&){return -2;}catch(...){return -3;}
}
