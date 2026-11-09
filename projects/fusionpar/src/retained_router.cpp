#include "joint_state.hpp"

#include <algorithm>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <tuple>

namespace fusionpar::joint {
namespace {
struct NodeLink {Id parent, depth;std::uint64_t delay;};
struct Tree {
    Id source=invalid;
    std::map<Id,NodeLink> links;
    std::vector<std::size_t> tasks;
};
void bump(std::uint32_t& version) {
    if(version==0xffffffffU)throw std::overflow_error("retained router scratch version overflow");
    ++version;
}
std::uint16_t edge_delay(const Design& d,Id from,Id to) {
    const auto& n=d.nodes.at(from);
    for(Id i=0;i<n.edge_count;++i)if(d.edges.at(n.edge_begin+i).dst==to)return d.edges[n.edge_begin+i].delay_q;
    throw std::invalid_argument("retained tree uses absent edge");
}
void append(const Design& d,Tree& tree,Id from,const std::vector<Id>& path,bool existing) {
    for(Id node:path) {
        const auto parent=tree.links.at(from);
        NodeLink link{from,parent.depth+1,parent.delay+edge_delay(d,from,node)};
        const auto [it,inserted]=tree.links.emplace(node,link);
        if(!inserted && (!existing || it->second.parent!=from))
            throw std::invalid_argument("retained tree cycle/reentry/multiple parents");
        from=node;
    }
}
std::vector<Id> prefix(const Tree& tree,Id node) {
    std::vector<Id> path;
    for(std::size_t n=0;node!=tree.source;++n) {
        if(n>=tree.links.size())throw std::logic_error("retained tree cycle");
        path.push_back(node);node=tree.links.at(node).parent;
    }
    std::reverse(path.begin(),path.end());return path;
}
}

Router retained_cmodel_router(persistroute::PathfinderConfig config) {
    // This controller has fixed one-task issue width and a frozen timing epoch.
    // Refuse unsupported scheduling policies rather than silently ignoring them.
    if(!config.max_iterations || !config.present_multiplier_q || config.min_timing_iterations!=1 ||
       config.adaptive_issue_width_min || config.adaptive_issue_stagnation_iterations || config.adaptive_issue_tail_tasks)
        throw std::invalid_argument("unsupported retained router configuration");
    return [=](const RoutingRequest& req) {
        RoutingReply reply;
        const auto& d=req.design;
        auto resources=req.base_resources;
        if(resources.size()!=d.nodes.size())throw std::invalid_argument("retained resource size mismatch");
        std::map<Id,std::size_t> by_id;
        std::map<Id,Tree> trees;
        for(const auto& task:req.tasks) {
            if(task.source>=d.nodes.size() || task.sink>=d.nodes.size() || !by_id.emplace(task.id,reply.tasks.size()).second)
                throw std::invalid_argument("invalid retained routing task");
            auto& tree=trees[task.net_id];
            if(tree.source!=invalid && tree.source!=task.source)throw std::invalid_argument("retained net has multiple sources");
            tree.source=task.source;tree.links[task.source]={invalid,0,0};
            tree.tasks.push_back(reply.tasks.size());reply.tasks.push_back({task,{},false});
        }
        std::set<Id> fixed;
        if(req.retained)for(const auto& old:*req.retained) {
            const auto it=by_id.find(old.task.id);
            if(it==by_id.end() || !old.routed || !fixed.insert(old.task.id).second)throw std::invalid_argument("invalid retained connection identity");
            auto& routed=reply.tasks[it->second];const auto& t=routed.task;
            if(t.source!=old.task.source || t.sink!=old.task.sink || t.net_id!=old.task.net_id ||
               old.path.size()>t.max_hops || (old.path.empty()?t.source:old.path.back())!=t.sink)
                throw std::invalid_argument("retained endpoints/hop bound changed");
            auto& tree=trees.at(t.net_id);append(d,tree,tree.source,old.path,true);
            routed.path=old.path;routed.routed=true;
        }
        const auto frozen=trees;
        std::vector<std::set<Id>> owners(resources.size());
        auto track=[&](Id net,const Tree& tree,bool add) {
            for(const auto& entry:tree.links)if(entry.first!=tree.source) {
                if(add)owners.at(entry.first).insert(net);else owners.at(entry.first).erase(net);
            }
        };
        for(const auto& item:trees)track(item.first,item.second,true);
        auto refresh=[&]() {
            for(Id node=0;node<resources.size();++node) {
                const auto& base=req.base_resources[node];auto& value=resources[node];
                // Base contains only unaffected nets. Explicit per-net sets
                // retain exact shared accounting even for capacity > 1.
                const auto count=std::uint64_t(base.occupancy)+owners[node].size();
                if(count>=65535U)throw std::overflow_error("retained occupancy range exceeded");
                const Id owner=count==1?(base.occupancy?base.owner:*owners[node].begin()):invalid;
                if(value.occupancy!=count || value.owner!=owner) {
                    value.occupancy=static_cast<std::uint16_t>(count);value.owner=owner;bump(value.version);
                }
            }
        };
        refresh();
        // Same priority/id order and wave scheduling as the existing width=1
        // PR controller. Retention removes searches, not candidate priorities.
        auto task_less=[&](std::size_t a,std::size_t b) {
            const auto& x=reply.tasks[a].task;const auto& y=reply.tasks[b].task;
            return std::tie(x.priority,x.id)<std::tie(y.priority,y.id);
        };
        std::vector<Id> order;
        for(auto& item:trees){std::sort(item.second.tasks.begin(),item.second.tasks.end(),task_less);order.push_back(item.first);}
        std::sort(order.begin(),order.end(),[&](Id a,Id b){return task_less(trees[a].tasks.front(),trees[b].tasks.front());});
        std::set<Id> pending(order.begin(),order.end());
        std::uint16_t present=config.present_start_q;
        auto costs=[&](std::uint16_t history_step) {
            for(auto& r:resources) {
                const auto over=std::max<int>(0,int(r.occupancy)-r.capacity);
                const auto history=std::uint64_t(r.history_cost_q)+std::uint64_t(history_step)*over;
                if(history>=65535 || present==65535)throw std::overflow_error("retained numeric guard: congestion cost saturation");
                if(r.present_cost_q!=present || r.history_cost_q!=history) {
                    r.present_cost_q=present;r.history_cost_q=static_cast<std::uint16_t>(history);bump(r.version);
                }
            }
        };
        costs(0);
        const auto execute=guarded_cmodel_executor(d,req.tasks);
        std::set<Id> overused;
        for(Id iteration=0;iteration<config.max_iterations;++iteration) {
            reply.iterations=iteration+1;
            if(iteration) {
                for(Id net:pending) {
                    track(net,trees.at(net),false);
                    trees[net].links=frozen.at(net).links;track(net,trees[net],true);
                    for(auto index:trees[net].tasks)if(!fixed.count(reply.tasks[index].task.id)) {
                        reply.tasks[index].routed=false;reply.tasks[index].path.clear();
                    }
                }
                refresh();
            }
            std::map<Id,std::size_t> cursor;
            for(;;) {
                bool launched=false;
                for(Id net:order)if(pending.count(net)) {
                    auto& tree=trees.at(net);auto& pos=cursor[net];
                    while(pos<tree.tasks.size() && fixed.count(reply.tasks[tree.tasks[pos]].task.id))++pos;
                    if(pos==tree.tasks.size())continue;
                    launched=true;auto& routed=reply.tasks[tree.tasks[pos++]];auto task=routed.task;task.epoch=iteration;
                    std::vector<persistroute::SearchSeed> seeds;
                    for(const auto& entry:tree.links) {
                        const auto cost=entry.second.delay*task.criticality_q/65535U*config.route_tree_timing_weight_q/256U;
                        if(cost>=0xffffffffULL)throw std::overflow_error("retained numeric guard: seed cost overflow");
                        seeds.push_back({entry.first,entry.second.depth,static_cast<Id>(cost)});
                    }
                    auto batch=execute(d.nodes,d.edges,resources,{task},{seeds},true);
                    ++reply.kernel_searches;reply.expanded+=batch.search_metrics.expanded;reply.edge_visits+=batch.search_metrics.edge_visits;
                    if(batch.candidates.size()!=1)throw std::logic_error("retained kernel omitted/added task");
                    const auto& result=batch.candidates.front();
                    if(result.task.id!=task.id)throw std::logic_error("retained kernel changed task identity");
                    if(result.search_status==1 && result.commit_status==4) {
                        if(!tree.links.count(result.attachment) ||
                           (result.path.empty()?result.attachment:result.path.back())!=task.sink)
                            throw std::logic_error("retained kernel returned invalid attachment/sink");
                        routed.path=prefix(tree,result.attachment);
                        append(d,tree,result.attachment,result.path,false);
                        routed.path.insert(routed.path.end(),result.path.begin(),result.path.end());
                        if(routed.path.size()>task.max_hops)throw std::logic_error("retained kernel exceeded hop bound");
                        routed.routed=true;for(Id node:result.path)owners[node].insert(net);
                    }
                    refresh();
                }
                if(!launched)break;
            }
            overused.clear();for(Id n=0;n<resources.size();++n)if(resources[n].occupancy>resources[n].capacity)overused.insert(n);
            if(overused.empty() && std::all_of(reply.tasks.begin(),reply.tasks.end(),[](const auto& task){return task.routed;})) {
                reply.success=true;return reply;
            }
            if(iteration+1==config.max_iterations)break;
            pending.clear();for(const auto& task:reply.tasks)if(!task.routed)pending.insert(task.task.net_id);
            for(Id node:overused)pending.insert(owners[node].begin(),owners[node].end());
            const auto grown=(std::uint64_t(present)*config.present_multiplier_q+128U)/256U;
            if(grown>=65535)throw std::overflow_error("retained numeric guard: present cost saturation");
            present=static_cast<std::uint16_t>(std::max<std::uint64_t>(1,grown));costs(config.history_increment_q);
        }
        reply.detail="retained controller exhausted routing budget";reply.feedback.kind=FeedbackKind::routing;
        reply.feedback.resource_ids.assign(overused.begin(),overused.end());
        for(const auto& task:reply.tasks)if(!task.routed || std::any_of(task.path.begin(),task.path.end(),[&](Id n){return overused.count(n);}))
            reply.feedback.connection_ids.push_back(task.task.id);
        return reply;
    };
}
} // namespace fusionpar::joint
