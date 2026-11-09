#pragma once
#include "native_corridor.hpp"
#include "native_die_access.hpp"
#include "native_worker_shadows.hpp"
#include <future>
#include <chrono>
namespace dieroute {
struct NativeNetTask {std::uint32_t id,sink,sink_die;};
struct NativeNetBranch {
    NativeNetTask task;
    std::size_t pass=0;
    bool rescue=false,deferred=false;
    SparseSearchResult result;
    bool shadow_path=false;
};
struct NativeNetPass {std::size_t pass,before,after,failed,deferred;bool rescue,retry;};
struct NativeNetProposal {
    std::uint32_t net=UINT32_MAX;
    std::uint64_t present=0,expanded=0,edge_visits=0,quotient_expanded=0,quotient_edge_visits=0;
    std::uint64_t label_packets=0,begin_ns=0,end_ns=0;
    std::size_t max_labels=0,deferred_retries=0;
    std::shared_ptr<const NativeRouteState> snapshot;
    std::vector<std::uint32_t> reads;
    std::vector<NativeNetBranch> branches;
    std::vector<NativeNetPass> passes;
    std::map<std::uint32_t,SparseSearchStatus> statuses;
    std::vector<NativeShadowRead> shadow_reads;
    std::vector<NativeSummaryPacket> shadow_messages;
    bool overflow=false;
};
// Record every dynamic cost observation, including absent and off-path nodes.
// Bit membership avoids one allocation/map lookup per observed resource.
class NativeReadFootprint {
    std::vector<std::uint64_t> bits_;
    std::vector<std::uint32_t> nodes_;
    std::uint64_t count_;
public:
    explicit NativeReadFootprint(std::uint64_t count):bits_((count+63)/64),count_(count){
        if(count>UINT32_MAX)throw std::invalid_argument("native read footprint range");
    }
    void read(std::uint32_t n){
        if(n>=count_)throw std::out_of_range("native read footprint node");
        const auto bit=std::uint64_t(1)<<(n%64);
        if(!(bits_[n/64]&bit)){bits_[n/64]|=bit;nodes_.push_back(n);}
    }
    auto finish(){std::sort(nodes_.begin(),nodes_.end());return std::move(nodes_);}
};
inline bool native_same_tree(const NativeTree& a,const NativeTree& b){
    if(a.source!=b.source||a.nodes.size()!=b.nodes.size())return false;
    auto x=a.nodes.begin(),y=b.nodes.begin();
    for(;x!=a.nodes.end();++x,++y)if(x->first!=y->first||
        std::tie(x->second.parent,x->second.pip,x->second.depth)!=std::tie(y->second.parent,y->second.pip,y->second.depth))return false;
    return true;
}
inline bool native_same_use(const NativeUse* a,const NativeUse* b){
    const NativeUse empty{};if(!a)a=&empty;if(!b)b=&empty;
    return a->version==b->version&&a->history==b->history&&a->nets==b->nets;
}
struct NativeNetValidation {bool tree_changed=false;std::vector<std::uint32_t> conflicts;std::vector<std::size_t> stale_shadows;bool valid()const{return !tree_changed&&conflicts.empty()&&stale_shadows.empty();}};
inline NativeNetValidation native_validate_net(const NativeRouteState& current,const NativeNetProposal& p,std::uint64_t present){
    if(!p.snapshot||p.present!=present||!current.layout().same(p.snapshot->layout()))throw std::logic_error("native transaction context mismatch");
    if(!std::is_sorted(p.reads.begin(),p.reads.end())||std::adjacent_find(p.reads.begin(),p.reads.end())!=p.reads.end())throw std::logic_error("noncanonical native read set");
    NativeNetValidation result;
    result.tree_changed=!current.trees().count(p.net)||!p.snapshot->trees().count(p.net)||!native_same_tree(current.tree(p.net),p.snapshot->tree(p.net));
    for(auto n:p.reads)if(!native_same_use(current.find_use(n),p.snapshot->find_use(n)))result.conflicts.push_back(n);
    for(std::size_t i=0;i<p.shadow_reads.size();++i){const auto& r=p.shadow_reads[i];
        if(!std::binary_search(p.reads.begin(),p.reads.end(),r.node))throw std::logic_error("shadow observation missing from footprint");
        if(!(r.seen==NativeWorkerShadows::authority(current,r.node)))result.stale_shadows.push_back(i);
    }
    return result;
}
// Publication happens only after all search threads have joined. Copying here
// is a CPU reference rollback buffer, not a second authoritative owner/HBM map.
// All branches are staged before one swap; any late error leaves current intact.
template<class Allowed,class EdgeValid>
bool native_commit_net(NativeRouteState& current,const NativeNetProposal& p,std::uint64_t present,Allowed allowed,EdgeValid edge_valid){
    if(!native_validate_net(current,p,present).valid())return false;
    if(p.overflow)throw std::overflow_error("current native net proposal overflow");
    NativeRouteState staged(current);bool changed=false;
    for(const auto& branch:p.branches)if(branch.result.status==SparseSearchStatus::found){
        std::uint64_t cost=0;
        for(auto n:branch.result.path){
            if(!std::binary_search(p.reads.begin(),p.reads.end(),n))throw std::logic_error("native write missing from read set");
            auto delta=staged.cost(n,p.net,present);
            if(delta>=UINT64_MAX-cost)throw std::overflow_error("native commit cost overflow");
            cost+=delta;
        }
        if(cost!=branch.result.cost)throw std::logic_error("native proposal cost changed");
        staged.accept(p.net,branch.task.sink,branch.result,allowed,edge_valid);changed=true;
    }
    if(changed)current.swap(staged);
    return true;
}
// Distinct whole nets search concurrently on the same immutable authority
// snapshot. Futures are all joined before the caller may validate or commit.
template<class Execute>
std::vector<NativeNetProposal> native_parallel_propose(const std::vector<std::uint32_t>& nets,Execute execute){
    if(std::set<std::uint32_t>(nets.begin(),nets.end()).size()!=nets.size())throw std::invalid_argument("duplicate net in speculative window");
    std::vector<std::future<NativeNetProposal>> futures;futures.reserve(nets.size());
    for(std::size_t slot=0;slot<nets.size();++slot)futures.push_back(std::async(std::launch::async,[&,slot]{
        const auto begin=std::chrono::steady_clock::now();auto result=execute(slot,nets[slot]);
        result.begin_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(begin.time_since_epoch()).count();
        result.end_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();return result;
    }));
    std::vector<NativeNetProposal> results;results.reserve(nets.size());
    for(auto& f:futures)results.push_back(f.get());
    return results;
}
// The serial within-net task/pass/rescue policy is the existing native cohort
// policy. Only independent nets are overlapped; shared-tree growth is local.
template<class Expand,class Membership,class Allowed,class EdgeValid,class Prepare,class Potential,class Rank>
NativeNetProposal native_propose_net(std::shared_ptr<const NativeRouteState> snapshot,std::uint32_t net,
    const std::vector<NativeNetTask>& tasks,std::uint64_t present,std::uint64_t node_count,std::size_t limit,
    NativeCorridorRouter& corridor,SparseSearch& search,Expand expand,Membership membership,Allowed allowed,
    EdgeValid edge_valid,Prepare prepare,Potential potential,Rank rank,bool defer_budget=true,NativeWorkerShadows* shadows=nullptr){
    NativeNetProposal p;p.net=net;p.present=present;p.snapshot=std::move(snapshot);
    NativeRouteState local(*p.snapshot);NativeReadFootprint reads(node_count);
    for(const auto& task:tasks)if(!p.statuses.emplace(task.id,SparseSearchStatus::exhausted).second)throw std::invalid_argument("duplicate native net task");
    try{
        bool retry=true,rescue=false;std::size_t pass=0;
        while(retry){const auto before=local.tree(net).nodes.size();std::size_t failed=0,deferred=0;
            auto mode=defer_budget?(rescue?NativeFallbackMode::flat_rescue:NativeFallbackMode::defer_budget):NativeFallbackMode::immediate;
            for(const auto& task:tasks){
                if(pass&&p.statuses.at(task.id)==SparseSearchStatus::found)continue;
                if(pass)++p.deferred_retries;
                NativeNetBranch b;b.task=task;b.pass=pass;b.rescue=rescue;
                if(local.tree(net).nodes.count(task.sink)){
                    b.result.status=SparseSearchStatus::found;b.result.attachment=task.sink;b.result.hops=local.tree(net).nodes.at(task.sink).depth;
                }else{
                    NativeDieAccess access(local,net,present);const auto old_deferred=corridor.metrics().budget_deferrals;
                    const auto old_expanded=p.expanded,old_visits=p.edge_visits;
                    try{b.result=corridor.run(local,net,task.sink,task.sink_die,node_count,search,{limit,UINT64_MAX},expand,membership,
                        [&](auto n){return allowed(n,net);},[&](auto n,auto die){reads.read(n);
                            if(shadows&&die!=UINT32_MAX&&die!=local.owner(n)){
                                auto [value,hit]=shadows->query(*p.snapshot,die,n);p.shadow_reads.push_back({p.branches.size(),die,n,value,hit});
                                return NativeWorkerShadows::cost(value,p.snapshot->tree(net).nodes.count(n),present);
                            }
                            return die==UINT32_MAX?local.cost(n,net,present):access.cost(die,n,membership(n));},
                        prepare,potential,rank,p.expanded,p.edge_visits,p.max_labels,mode);
                    }catch(...){for(const auto& attempt:corridor.trace())p.label_packets+=attempt.packets.size();throw;}
                    if(!access.validate())throw std::logic_error("immutable native transaction read phase invalidated");
                    b.result.expanded=p.expanded-old_expanded;b.result.edge_visits=p.edge_visits-old_visits;
                    b.deferred=corridor.metrics().budget_deferrals>old_deferred;
                    if(shadows)for(const auto& attempt:corridor.trace())b.shadow_path|=attempt.selected;
                    for(const auto& attempt:corridor.trace()){
                        p.label_packets+=attempt.packets.size();
                        for(auto n:attempt.portals)if(n!=UINT32_MAX)reads.read(n);
                    }
                }
                p.statuses.at(task.id)=b.result.status;
                if(b.result.status==SparseSearchStatus::found){
                    for(auto n:b.result.path)reads.read(n);
                    local.accept(net,task.sink,b.result,allowed,edge_valid);
                }else{++failed;deferred+=b.deferred;}
                p.branches.push_back(std::move(b));
            }
            const auto after=local.tree(net).nodes.size();retry=failed&&after>before;
            const bool enter_rescue=defer_budget&&!rescue&&deferred&&after==before;
            if(enter_rescue)retry=true;
            p.passes.push_back({pass,before,after,failed,deferred,rescue,retry});
            if(enter_rescue)rescue=true;
            ++pass;
        }
    }catch(const std::overflow_error&){p.overflow=true;}
    p.reads=reads.finish();if(shadows)p.shadow_messages=shadows->take_messages();return p;
}
}
