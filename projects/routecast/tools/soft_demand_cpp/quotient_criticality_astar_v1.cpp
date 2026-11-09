#include "criticality_tree_exact_v2.cpp"
#include <tuple>

struct AWorkspace: Workspace {
    U groups;
    std::vector<U> hseen;
    std::vector<Big> hcache;
    using AItem=std::tuple<Big,Big,U>; // f, actual g, original node ID.
    std::vector<AItem> aheap;
    AWorkspace(U n,U m):Workspace(n),groups(m),hseen(m),hcache(m){}
};
static Big quad(const U* values,U group) {
    Big out;
    for(unsigned i=0;i<4;++i)out.v[i]=values[4*group+i];
    return out;
}
static Big checked_key(const Big& cost,const Big& h) {
    Big out=cost+h;
    if(out.v[3]>>48)throw std::overflow_error("A* key exceeds240 bits");
    return out;
}
extern "C" void* rc_quotient_create(U n,U m) {
    try {return n&&m?new AWorkspace(n,m):nullptr;}catch(...){return nullptr;}
}
extern "C" void rc_quotient_destroy(void* handle) {delete static_cast<AWorkspace*>(handle);}
extern "C" int rc_quotient_expand(void* handle,U target,U p,U q,
    const U* row,const U* dest,const Word* increment,
    const U* seed_nodes,const Word* seed_arrival,U seed_count,
    const Word* base,const Word* prices,U* path,U path_capacity,Result* result,U* stats,
    const U* groups,const U* raw_h,const U* floor_h,const U* reachable) {
    try {
        auto* w=static_cast<AWorkspace*>(handle);
        if(!w||target>=w->n||!q||p>q||!seed_count||!result||!stats||path_capacity<w->n)return -1;
        const U n=w->n;
        if(++w->epoch==0) {
            for(auto* a:{&w->seen,&w->visited,&w->seed,&w->priced,&w->hseen})std::fill(a->begin(),a->end(),0);
            w->epoch=1;
        }
        const U epoch=w->epoch;
        auto group_of=[&](U node){U group=groups[node];if(group>=w->groups)throw std::invalid_argument("group");return group;};
        auto heuristic=[&](U node)->const Big& {
            U group=group_of(node);
            if(w->hseen[group]!=epoch) {
                w->hcache[group]=multiply(quad(raw_h,group),p)+multiply(quad(floor_h,group),q-p);
                w->hseen[group]=epoch;
            }
            return w->hcache[group];
        };
        std::fill(stats,stats+4,U(0));
        auto& heap=w->aheap;heap.clear();std::greater<AWorkspace::AItem> greater;
        for(U i=0;i<seed_count;++i) {
            U u=seed_nodes[i];if(u>=n||w->seed[u]==epoch)return -1;
            w->seed[u]=w->seen[u]=epoch;w->seed_raw[u]=big(seed_arrival[i]);
            if(!reachable[group_of(u)])continue;
            w->dist[u]=multiply(w->seed_raw[u],p);
            heap.emplace_back(checked_key(w->dist[u],heuristic(u)),w->dist[u],u);++stats[2];
        }
        std::make_heap(heap.begin(),heap.end(),greater);
        bool found=false;
        while(!heap.empty()) {
            std::pop_heap(heap.begin(),heap.end(),greater);auto item=heap.back();heap.pop_back();
            U u=std::get<2>(item);const Big& cost=std::get<1>(item);
            if(w->visited[u]==epoch||cost!=w->dist[u])continue;
            w->visited[u]=epoch;++stats[0];
            if(u==target){found=true;break;}
            for(U slot=row[u];slot<row[u+1];++slot) {
                ++stats[1];U v=dest[slot];if(v>=n)return -1;
                if(w->seed[v]==epoch||w->visited[v]==epoch||!reachable[group_of(v)])continue;
                if(w->priced[v]!=epoch) {
                    w->price[v]=multiply(big(base[v])+big(prices[v]),q-p);w->priced[v]=epoch;
                }
                Big next=cost+multiply(big(increment[slot]),p)+w->price[v];
                if(w->seen[v]!=epoch||next<w->dist[v]) {
                    w->seen[v]=epoch;w->dist[v]=next;w->pn[v]=u;w->pe[v]=slot;
                    heap.emplace_back(checked_key(next,heuristic(v)),next,v);
                    std::push_heap(heap.begin(),heap.end(),greater);++stats[2];
                }
            }
        }
        stats[3]=heap.capacity();if(!found)return 1;
        U u=target,count=0;Big extra=0;
        while(w->seed[u]!=epoch) {
            if(count>=n)return -1;
            U slot=w->pe[u];path[count++]=slot;extra+=big(increment[slot]);u=w->pn[u];
        }
        std::reverse(path,path+count);result->attach=u;result->count=count;
        result->raw=word(w->seed_raw[u]+extra);
        for(unsigned i=0;i<4;++i)result->objective[i]=w->dist[target].v[i];
        return 0;
    }catch(const std::overflow_error&){return -2;}catch(...){return -3;}
}
