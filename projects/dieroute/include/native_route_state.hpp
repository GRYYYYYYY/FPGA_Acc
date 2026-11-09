#pragma once
#include "sparse_search.hpp"
#include <array>
#include <functional>
#include <memory>
#include <map>
#include <set>

namespace dieroute {
// Serial sparse authority for electrical nodes. A legal solution has one net
// per electrical node; multiple sinks on the same net count once. This does
// not model site/mux constraints, timing, general RR capacities or hardware.
struct NativeUse {
    std::set<std::uint32_t> nets;
    std::uint64_t history=0,version=0;
};
struct NativeTreeNode {
    std::uint32_t parent=UINT32_MAX,pip=UINT32_MAX,depth=0;
};
struct NativeTree {
    std::uint32_t source=UINT32_MAX;
    std::map<std::uint32_t,NativeTreeNode> nodes;
};
// The membership provider must refer to immutable topology and remain alive for
// all copies of this layout. Electrical nodes retain their full membership;
// only their mutable authority is assigned to the lowest member die.
class NativeOwnerLayout {
    struct Policy {
        std::uint32_t count;
        std::function<std::uint32_t(std::uint32_t)> membership;
    };
    std::shared_ptr<const Policy> policy_;
public:
    NativeOwnerLayout()=default; // single centralized owner, for the control arm
    template<class Membership>
    static NativeOwnerLayout from_membership(std::uint32_t count,Membership membership){
        if(!count||count>8)throw std::invalid_argument("invalid native owner count");
        NativeOwnerLayout result;
        result.policy_=std::make_shared<const Policy>(Policy{count,std::move(membership)});
        return result;
    }
    std::uint32_t count()const{return policy_?policy_->count:1;}
    std::uint32_t membership(std::uint32_t node)const{
        if(node==UINT32_MAX)throw std::invalid_argument("invalid native owner node");
        if(!policy_)return 1;
        const auto mask=policy_->membership(node);
        if(!mask||mask>=(1u<<count()))throw std::invalid_argument("invalid native owner membership");
        return mask;
    }
    std::uint32_t owner(std::uint32_t node)const{
        const auto mask=membership(node);
        std::uint32_t die=0;while(!(mask&(1u<<die)))++die;return die;
    }
    bool same(const NativeOwnerLayout& other)const{return policy_==other.policy_;}
    void swap(NativeOwnerLayout& other)noexcept{policy_.swap(other.policy_);}
};
class NativeRouteState {
    using Uses=std::map<std::uint32_t,NativeUse>;
    NativeOwnerLayout layout_;
    std::array<Uses,8> shards_; // sole mutable copies; no global resource map/index
    std::map<std::uint32_t,NativeTree> trees_;
    std::shared_ptr<const unsigned char> revision_=std::make_shared<const unsigned char>(0);
    static void require(bool ok,const char* what){if(!ok)throw std::logic_error(what);}
    static void incrementable(const NativeUse& u){if(u.version==UINT64_MAX)throw std::overflow_error("native version exhausted");}
    // Route and allocate the entire delta before the first authoritative write.
    // Publication then transfers preallocated map nodes or swaps existing sets.
    // This is serial logical atomicity, not a concurrent distributed protocol.
    void publish(Uses& staged){
        auto next=std::make_shared<const unsigned char>(0);
        std::array<Uses,8> deltas;
        while(!staged.empty()){
            auto it=staged.begin();const auto die=owner(it->first);
            deltas[die].insert(staged.extract(it));
        }
        for(std::uint32_t die=0;die<owner_count();++die){auto& target=shards_[die];auto& delta=deltas[die];
            for(auto it=delta.begin();it!=delta.end();){auto current=target.find(it->first);
                if(current==target.end())target.insert(delta.extract(it++));
                else {current->second.nets.swap(it->second.nets);current->second.history=it->second.history;
                    current->second.version=it->second.version;++it;}}
        }
        revision_.swap(next);
    }
public:
    NativeRouteState()=default;
    explicit NativeRouteState(NativeOwnerLayout layout):layout_(std::move(layout)){}
    NativeRouteState(const NativeRouteState& other):layout_(other.layout_),shards_(other.shards_),trees_(other.trees_){}
    NativeRouteState(NativeRouteState&&)=default;
    NativeRouteState& operator=(const NativeRouteState& other){if(this!=&other){NativeRouteState copy(other);swap(copy);}return *this;}
    NativeRouteState& operator=(NativeRouteState&&)=default;
    auto revision()const{return revision_;}
    void swap(NativeRouteState& other) noexcept {revision_.swap(other.revision_);layout_.swap(other.layout_);shards_.swap(other.shards_);trees_.swap(other.trees_);}
    const NativeOwnerLayout& layout()const{return layout_;}
    std::uint32_t owner_count()const{return layout_.count();}
    std::uint32_t owner(std::uint32_t node)const{return layout_.owner(node);}
    const Uses& owner_uses(std::uint32_t die)const{
        require(die<owner_count(),"invalid native owner shard");return shards_[die];
    }
    const NativeUse* owner_use(std::uint32_t die,std::uint32_t node)const{
        require(die<owner_count()&&die==owner(node),"non-owner native access");
        const auto& shard=shards_[die];auto it=shard.find(node);return it==shard.end()?nullptr:&it->second;
    }
    const NativeUse* find_use(std::uint32_t node)const{
        const auto& shard=shards_[owner(node)];auto it=shard.find(node);return it==shard.end()?nullptr:&it->second;
    }
    const NativeUse& use(std::uint32_t node)const{
        auto value=find_use(node);if(!value)throw std::out_of_range("missing native use");return *value;
    }
    std::size_t use_count()const{std::size_t n=0;for(const auto& shard:shards_)n+=shard.size();return n;}
    // Merge at most eight sorted shards without allocating/copying authority.
    // Canonical node order preserves existing journals and checkpoint bytes.
    template<class Emit> void visit_uses(Emit emit)const{
        std::array<Uses::const_iterator,8> next;
        for(std::uint32_t d=0;d<owner_count();++d)next[d]=shards_[d].begin();
        while(true){std::uint32_t best=owner_count();
            for(std::uint32_t d=0;d<owner_count();++d)
                if(next[d]!=shards_[d].end()&&(best==owner_count()||next[d]->first<next[best]->first))best=d;
            if(best==owner_count())break;
            emit(next[best]->first,next[best]->second);++next[best];
        }
    }
    Uses snapshot_uses()const{Uses result;visit_uses([&](auto n,const auto& u){result.emplace(n,u);});return result;}
    // Import a complete checkpoint, including unused history/version records.
    // A strict depth increase proves parent chains terminate at the sole root.
    template<class Allowed,class EdgeValid>
    static NativeRouteState checkpoint(std::map<std::uint32_t,NativeTree> trees,
                                      std::map<std::uint32_t,NativeUse> uses,
                                      Allowed allowed,EdgeValid edge_valid,NativeOwnerLayout layout={}){
        std::map<std::uint32_t,std::set<std::uint32_t>> expected;
        for(const auto& [net,t]:trees){
            require(net!=UINT32_MAX&&t.source!=UINT32_MAX&&t.nodes.count(t.source),"invalid checkpoint root/net");
            for(const auto& [n,v]:t.nodes){
                require(n!=UINT32_MAX&&allowed(n,net),"forbidden checkpoint node");expected[n].insert(net);
                if(n==t.source)require(v.parent==UINT32_MAX&&v.pip==UINT32_MAX&&v.depth==0,"invalid checkpoint root record");
                else {auto parent=t.nodes.find(v.parent);
                    require(parent!=t.nodes.end()&&parent->second.depth<UINT32_MAX&&v.depth==parent->second.depth+1,
                            "invalid checkpoint parent/depth");
                    require(v.pip!=UINT32_MAX&&edge_valid(v.parent,n,v.pip),"invalid checkpoint PIP");}
            }
        }
        for(const auto& [n,u]:uses){
            require(n!=UINT32_MAX&&u.history!=UINT64_MAX,"invalid checkpoint use");
            const auto it=expected.find(n);
            require(it==expected.end()?u.nets.empty():u.nets==it->second,"checkpoint ownership disagreement");
        }
        for(const auto& [n,nets]:expected){(void)nets;require(uses.count(n),"missing checkpoint use");}
        NativeRouteState result(std::move(uses),std::move(layout));result.trees_=std::move(trees);return result;
    }
    explicit NativeRouteState(Uses initial,NativeOwnerLayout layout={}):layout_(std::move(layout)){
        for(const auto& [node,u]:initial){(void)node;require(u.history!=UINT64_MAX,"nonfinite native history");}
        publish(initial);
    }
    const auto& trees()const{return trees_;}
    const NativeTree& tree(std::uint32_t net)const{return trees_.at(net);}
    template<class Allowed> void start(std::uint32_t net,std::uint32_t source,Allowed allowed){
        require(net!=UINT32_MAX&&source!=UINT32_MAX&&allowed(source,net),"forbidden native source");require(!trees_.count(net),"duplicate native net");
        std::map<std::uint32_t,NativeTree> treeStage;treeStage[net].source=source;treeStage[net].nodes.emplace(source,NativeTreeNode{});
        std::map<std::uint32_t,NativeUse> staged;auto found=find_use(source);NativeUse value=found?*found:NativeUse{};
        require(value.nets.empty()||(value.nets.size()==1&&value.nets.count(net)),"occupied native source");
        if(!value.nets.count(net)){incrementable(value);value.nets.insert(net);++value.version;staged.emplace(source,std::move(value));}
        publish(staged);trees_.merge(treeStage);
    }
    std::vector<SparseSeed> seeds(std::uint32_t net)const{
        std::vector<SparseSeed> out;out.reserve(tree(net).nodes.size());
        for(const auto& [node,value]:tree(net).nodes)out.push_back({node,value.depth,0});
        return out;
    }
    std::uint64_t cost(std::uint32_t node,std::uint32_t net,std::uint64_t present)const{
        const auto found=find_use(node);if(!found)return 1;
        const auto& u=*found;const auto others=u.nets.size()-u.nets.count(net);
        if(u.history>=UINT64_MAX-1 || (others && present>(UINT64_MAX-2-u.history)/others))throw std::overflow_error("native negotiated cost overflow");
        return 1+u.history+present*others;
    }
    template<class Allowed,class EdgeValid> void accept(std::uint32_t net,std::uint32_t sink,const SparseSearchResult& branch,Allowed allowed,EdgeValid edge_valid){
        auto& t=trees_.at(net);require(branch.status==SparseSearchStatus::found&&branch.path.size()==branch.edges.size(),"invalid native branch result");
        require(t.nodes.count(branch.attachment)&&allowed(branch.attachment,net),"invalid native attachment");
        require((branch.path.empty()?branch.attachment:branch.path.back())==sink,"native branch misses sink");
        std::map<std::uint32_t,NativeTreeNode> newNodes;std::map<std::uint32_t,NativeUse> staged;
        auto parent=branch.attachment;auto depth=t.nodes.at(parent).depth;
        for(std::size_t i=0;i<branch.path.size();++i){auto node=branch.path[i];
            require(!t.nodes.count(node)&&!newNodes.count(node),"native tree reentry/cycle");require(allowed(node,net)&&edge_valid(parent,node,branch.edges[i]),"forbidden native branch/PIP");
            if(depth==UINT32_MAX)throw std::overflow_error("native tree depth overflow");
            ++depth;newNodes.emplace(node,NativeTreeNode{parent,branch.edges[i],depth});
            const auto found=find_use(node);NativeUse value=found?*found:NativeUse{};
            require(!value.nets.count(net),"native owner missing from its tree");incrementable(value);value.nets.insert(net);++value.version;staged.emplace(node,std::move(value));parent=node;
        }
        require(depth==branch.hops,"native branch depth disagreement");
        publish(staged);t.nodes.merge(newNodes);
    }
    void ripup(std::uint32_t net){
        auto next=std::make_shared<const unsigned char>(0);
        auto& t=trees_.at(net);
        std::vector<NativeUse*> pending;pending.reserve(t.nodes.size());
        for(const auto& [node,unused]:t.nodes)if(node!=t.source){(void)unused;auto& u=shards_[owner(node)].at(node);
            require(u.nets.count(net),"missing native owner at ripup");incrementable(u);pending.push_back(&u);}
        for(auto u:pending){u->nets.erase(net);++u->version;}
        for(auto it=t.nodes.begin();it!=t.nodes.end();)if(it->first!=t.source)it=t.nodes.erase(it);else ++it;
        revision_.swap(next);
    }
    std::set<std::uint32_t> negotiate(std::uint64_t increment){
        auto next=std::make_shared<const unsigned char>(0);
        std::set<std::uint32_t> pending;
        for(const auto& shard:shards_)for(const auto& [node,u]:shard)if(u.nets.size()>1){(void)node;auto excess=u.nets.size()-1;
            if(increment>(UINT64_MAX-1-u.history)/excess)throw std::overflow_error("native history overflow");
            if(increment){incrementable(u);}pending.insert(u.nets.begin(),u.nets.end());}
        for(auto& shard:shards_)for(auto& [node,u]:shard)if(u.nets.size()>1&&increment){(void)node;u.history+=increment*(u.nets.size()-1);++u.version;}
        revision_.swap(next);return pending;
    }
    std::size_t overused()const{std::size_t n=0;for(const auto& shard:shards_)for(const auto& [node,u]:shard){(void)node;n+=u.nets.size()>1;}return n;}
    std::vector<std::pair<std::uint32_t,std::uint32_t>> path(std::uint32_t net,std::uint32_t sink)const{
        const auto& t=tree(net);std::vector<std::pair<std::uint32_t,std::uint32_t>> out;
        for(auto n=sink;n!=t.source;){const auto& value=t.nodes.at(n);out.push_back({n,value.pip});n=value.parent;require(out.size()<t.nodes.size(),"native parent cycle");}
        std::reverse(out.begin(),out.end());return out;
    }
};
} // namespace dieroute
