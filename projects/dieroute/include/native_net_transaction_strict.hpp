#pragma once
#include "native_net_transaction.hpp"

namespace dieroute {
// Development strict-SLL search profile, derived from native_propose_net.
// Keeps its complete-net pass/rescue policy; only occupied crossing nodes
// are filtered. Grant/commit validation remains separately required.
template<class Expand,class Membership,class Allowed,class EdgeValid,class Prepare,class Potential,class Rank>
NativeNetProposal native_propose_net_strict_sll(std::shared_ptr<const NativeRouteState> snapshot,std::uint32_t net,
    const std::vector<NativeNetTask>& tasks,std::uint64_t present,std::uint64_t node_count,std::size_t limit,
    NativeCorridorRouter& corridor,SparseSearch& search,Expand expand,Membership membership,Allowed allowed,
    EdgeValid edge_valid,Prepare prepare,Potential potential,Rank rank,bool defer_budget=true,NativeWorkerShadows* shadows=nullptr){
    NativeNetProposal p;p.net=net;p.present=present;p.snapshot=std::move(snapshot);
    NativeRouteState local(*p.snapshot);NativeReadFootprint reads(node_count);
    // Capacity rejections are dynamic observations too: record them before
    // filtering so another net's rip-up/commit forces proper version replay.
    auto strict_expand=[&](std::uint32_t source,auto emit){
        expand(source,[&](std::uint32_t destination,std::uint32_t edge,std::uint32_t die){
            auto mask=membership(destination);
            if(mask&(mask-1)){
                reads.read(destination);auto use=local.find_use(destination);
                if(use&&use->nets.size()>use->nets.count(net))return;
            }
            emit(destination,edge,die);
        });
    };
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
                    try{b.result=corridor.run(local,net,task.sink,task.sink_die,node_count,search,{limit,UINT64_MAX},strict_expand,membership,
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
