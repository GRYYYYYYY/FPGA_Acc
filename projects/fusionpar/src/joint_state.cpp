#include "joint_state.hpp"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <tuple>

namespace fusionpar::joint {
namespace {
using Clock = std::chrono::steady_clock;
std::uint64_t elapsed(Clock::time_point start) {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count();
}
template<class T> void advance(T& value) {
    if (value == std::numeric_limits<T>::max()) throw std::overflow_error("version overflow");
    ++value;
}
Id terminal(const Design& d, const State& s, Id instance, Id pin, bool source) {
    const auto& site = d.sites.at(s.placement.at(instance).site);
    for (const auto& t : site.terminals) if (t.pin == pin && t.source == source) return t.node;
    throw std::invalid_argument("site has no mapping for connection terminal");
}
void placement_check(const Design& d, const State& s) {
    if (s.placement.size()!=d.instances.size() || s.site_versions.size()!=d.sites.size())
        throw std::invalid_argument("placement/site count mismatch");
    std::set<Id> occupied;
    for (Id i=0; i<s.placement.size(); ++i) {
        const auto site=s.placement[i].site;
        const auto& inst=d.instances[i];
        if (site>=d.sites.size() || !occupied.insert(site).second || d.sites[site].type!=inst.type ||
            std::find(inst.allowed_sites.begin(),inst.allowed_sites.end(),site)==inst.allowed_sites.end())
            throw std::invalid_argument("site/type/region/unique occupancy violation");
    }
    for (const auto& macro:d.macros) {
        const auto& anchor=d.sites.at(s.placement.at(macro.anchor).site);
        for (const auto& member:macro.members) {
            const auto& site=d.sites.at(s.placement.at(member.instance).site);
            if (std::int64_t(site.x)-anchor.x!=member.dx || std::int64_t(site.y)-anchor.y!=member.dy ||
                std::int64_t(site.subtile)-anchor.subtile!=member.dsubtile)
                throw std::invalid_argument("macro relative position violation");
        }
    }
}
using Owners = std::vector<std::set<Id>>;
Owners owners(const Design& d, const State& s, const std::set<Id>& excluded = {}) {
    Owners out(d.nodes.size());
    if (s.routes.size()!=d.connections.size()) throw std::invalid_argument("route count mismatch");
    for (std::size_t i=0; i<s.routes.size(); ++i) {
        const Id net=d.connections[i].net;
        if (!excluded.count(net)) for (Id node:s.routes[i].path) out.at(node).insert(net);
    }
    return out;
}
void assign_owners(std::vector<persistroute::Resource>& resources, const Owners& use) {
    if (resources.size()!=use.size()) throw std::invalid_argument("resource count mismatch");
    for (std::size_t i=0;i<use.size();++i) {
        if (use[i].size()>65535) throw std::overflow_error("occupancy overflow");
        resources[i].occupancy=static_cast<std::uint16_t>(use[i].size());
        resources[i].owner=use[i].size()==1?*use[i].begin():invalid;
    }
}
void design_check(const Design& d) {
    if (d.nodes.empty() || d.nodes.size()>=invalid || d.edges.size()>=invalid ||
        d.connections.size()>=invalid || d.instances.size()>=invalid || d.sites.size()>=invalid)
        throw std::invalid_argument("invalid design dimensions");
    for (const auto& n:d.nodes)
        if (std::uint64_t(n.edge_begin)+n.edge_count>d.edges.size())
            throw std::invalid_argument("invalid CSR range");
    for (const auto& e:d.edges) if (e.dst>=d.nodes.size()) throw std::invalid_argument("invalid edge destination");
    std::set<std::tuple<std::int32_t,std::int32_t,std::int32_t>> positions;
    for (const auto& site:d.sites) {
        if (!positions.emplace(site.x,site.y,site.subtile).second) throw std::invalid_argument("duplicate physical site");
        std::set<std::pair<Id,bool>> pins;
        for (const auto& t:site.terminals)
            if (t.node>=d.nodes.size() || !pins.emplace(t.pin,t.source).second)
                throw std::invalid_argument("invalid/duplicate terminal mapping");
    }
    for (const auto& instance:d.instances) {
        if (instance.allowed_sites.empty()) throw std::invalid_argument("missing explicit legal sites");
        std::set<Id> seen;
        for (Id id:instance.allowed_sites)
            if (id>=d.sites.size() || d.sites[id].type!=instance.type || !seen.insert(id).second)
                throw std::invalid_argument("invalid legal site list");
    }
    std::map<Id,std::pair<Id,Id>> net_sources;
    std::map<std::pair<Id,Id>,Id> source_nets;
    std::set<std::pair<Id,Id>> sinks;
    for (const auto& c:d.connections) {
        if(c.net==invalid || c.source_instance>=d.instances.size() || c.sink_instance>=d.instances.size() || !c.max_hops)
            throw std::invalid_argument("invalid connection identity");
        auto source=std::make_pair(c.source_instance,c.source_pin);
        if ((!net_sources.emplace(c.net,source).second && net_sources.at(c.net)!=source) ||
            (!source_nets.emplace(source,c.net).second && source_nets.at(source)!=c.net) ||
            !sinks.emplace(c.sink_instance,c.sink_pin).second)
            throw std::invalid_argument("inconsistent net source or duplicate sink pin");
    }
    for (const auto& m:d.macros) {
        if (m.anchor>=d.instances.size()) throw std::invalid_argument("invalid macro anchor");
        for (const auto& member:m.members)
            if (member.instance>=d.instances.size()) throw std::invalid_argument("invalid macro member");
    }
}
void state_check(const Design& d, const State& s) {
    placement_check(d,s);
    if(s.resources.size()!=d.nodes.size() || s.routes.size()!=d.connections.size() ||
       s.criticalities.size()!=d.connections.size() || s.timing_basis_revision>s.revision)
        throw std::invalid_argument("state dimensions/timing basis mismatch");
    std::map<Id,Id> roots;
    std::map<std::pair<Id,Id>,Id> parents;
    for (Id i=0;i<d.connections.size();++i) {
        const auto& c=d.connections[i]; const auto& route=s.routes[i];
        if (route.source!=terminal(d,s,c.source_instance,c.source_pin,true) ||
            route.sink!=terminal(d,s,c.sink_instance,c.sink_pin,false) || route.path.size()>c.max_hops)
            throw std::invalid_argument("stale route terminal or hop bound");
        if (!roots.emplace(c.net,route.source).second && roots.at(c.net)!=route.source)
            throw std::invalid_argument("net has multiple RR roots");
        Id prev=route.source; std::set<Id> visited{prev};
        for (Id next:route.path) {
            if (next>=d.nodes.size() || !visited.insert(next).second)
                throw std::invalid_argument("route cycle or invalid node");
            const auto& n=d.nodes.at(prev); bool adjacent=false;
            for (Id e=0;e<n.edge_count;++e) if(d.edges[n.edge_begin+e].dst==next) adjacent=true;
            if(!adjacent) throw std::invalid_argument("route contains absent directed edge");
            const auto key=std::make_pair(c.net,next);
            if (!parents.emplace(key,prev).second && parents.at(key)!=prev)
                throw std::invalid_argument("net tree has multiple parents");
            prev=next;
        }
        if (prev!=route.sink) throw std::invalid_argument("route does not reach sink");
    }
    const auto use=owners(d,s);
    for (std::size_t i=0;i<use.size();++i) {
        const auto& r=s.resources[i];
        if(!r.capacity || use[i].size()!=r.occupancy || r.occupancy>r.capacity ||
           r.owner!=(use[i].size()==1?*use[i].begin():invalid))
            throw std::invalid_argument("resource accounting/capacity violation");
    }
}
std::uint64_t payload_size(const State& s) {
    std::uint64_t bytes=s.placement.size()*sizeof(Placement)+s.site_versions.size()*sizeof(std::uint32_t)+
        s.resources.size()*sizeof(persistroute::Resource)+s.criticalities.size()*sizeof(std::uint16_t);
    for(const auto& r:s.routes) bytes+=3*sizeof(Id)+r.path.size()*sizeof(Id);
    return bytes+3*sizeof(std::uint64_t);
}
} // namespace

const char* status_name(Status s) {
    switch(s) {
#define CASE(x) case Status::x:return #x
        CASE(ready); CASE(committed); CASE(invalid_move); CASE(placement_illegal);
        CASE(sketch_rejected); CASE(route_failed); CASE(candidate_invalid); CASE(quality_rejected);
        CASE(stale_state); CASE(stale_timing); CASE(foreign_transaction); CASE(consumed); CASE(budget_exhausted);
#undef CASE
    }
    return "unknown";
}
bool validate_state(const Design& d,const State& s,std::string& error) {
    try { design_check(d); state_check(d,s); error.clear(); return true; }
    catch(const std::exception& e) { error=e.what(); return false; }
}
void initialize_accounting(const Design& d,State& s) { assign_owners(s.resources,owners(d,s)); }

Engine::Engine(Design d,State s,Router router,Validator validator)
    :design_(std::move(d)),state_(std::make_shared<const State>(std::move(s))),
     router_(std::move(router)),validator_(std::move(validator)) {
    if(!router_) throw std::invalid_argument("missing router");
    design_check(design_); state_check(design_,*state_);
    std::string detail;
    if(validator_ && !validator_(design_,*state_,detail)) throw std::invalid_argument("initial native validation: "+detail);
}

Transaction Engine::prepare(const Proposal& p,const Sketch& sketch,const Acceptance& accept,bool reroute_all,bool retain_branches) {
    return prepare_impl(p,sketch,accept,reroute_all,retain_branches,false);
}
Transaction Engine::prepare_routing(const Acceptance& accept) {
    return prepare_impl({}, {},accept,true,false,true);
}
Transaction Engine::prepare_impl(const Proposal& p,const Sketch& sketch,const Acceptance& accept,bool reroute_all,bool retain_branches,bool routing_epoch) {
    const auto begin=Clock::now();
    Transaction tx; tx.origin_=identity_; tx.base_=state_; tx.proposal_=p;
    auto finish=[&](Status status,const std::string& detail) -> Transaction {
        tx.status_=status; tx.detail_=detail; tx.metrics_.prepare_ns=elapsed(begin); return std::move(tx);
    };
    if(p.moves.empty() && !routing_epoch) return finish(Status::invalid_move,"empty proposal");
    if(reroute_all && retain_branches)return finish(Status::invalid_move,"global reroute conflicts with branch retention");
    std::set<Id> changed, changed_sites;
    for(const auto& m:p.moves) {
        if(m.instance>=design_.instances.size() || m.new_site>=design_.sites.size() ||
           !changed.insert(m.instance).second || m.old_site==m.new_site || design_.instances[m.instance].fixed)
            return finish(Status::invalid_move,"invalid/duplicate/fixed/no-op move");
        const auto& old=state_->placement[m.instance];
        if(old.site!=m.old_site || old.version!=m.observed_version)
            return finish(Status::stale_state,"proposal placement version/site mismatch");
        changed_sites.insert(m.old_site); changed_sites.insert(m.new_site);
    }
    const auto copy_begin=Clock::now();
    tx.candidate_=std::make_unique<State>(*state_);
    tx.metrics_.snapshot_ns=elapsed(copy_begin);
    tx.metrics_.copied_payload_bytes=payload_size(*state_);
    auto& candidate=*tx.candidate_;
    try {
        for(const auto& m:p.moves) { auto& v=candidate.placement[m.instance]; v.site=m.new_site; advance(v.version); }
        for(Id site:changed_sites) advance(candidate.site_versions[site]);
        placement_check(design_,candidate);
    } catch(const std::exception& e) { return finish(Status::placement_illegal,e.what()); }
    if(sketch && !sketch(design_,candidate,p)) return finish(Status::sketch_rejected,"sketch veto");
    std::set<Id> affected;
    for(const auto& c:design_.connections)
        if(reroute_all || changed.count(c.source_instance)||changed.count(c.sink_instance)) affected.insert(c.net);
    tx.metrics_.affected_nets=affected.size();
    std::vector<persistroute::Task> tasks;
    std::vector<persistroute::RoutedTask> retained;
    try {
        for(Id i=0;i<design_.connections.size();++i) {
            const auto& c=design_.connections[i]; if(!affected.count(c.net)) continue;
            for(Id node:state_->routes[i].path)
                if(state_->resources[node].version==0xffffffffU)
                    return finish(Status::candidate_invalid,"resource version would overflow on publication");
            tasks.push_back({i,c.net,terminal(design_,candidate,c.source_instance,c.source_pin,true),
                terminal(design_,candidate,c.sink_instance,c.sink_pin,false),candidate.criticalities[i],c.max_hops,c.priority,0,0});
            const auto& old=state_->routes[i];
            if(retain_branches && old.source==tasks.back().source && old.sink==tasks.back().sink) {
                retained.push_back({tasks.back(),old.path,true});
                tx.metrics_.retained_connections.push_back(i);
                tx.metrics_.copied_payload_bytes+=old.path.size()*sizeof(Id)+sizeof(persistroute::RoutedTask);
            }
        }
    } catch(const std::exception& e) { return finish(Status::placement_illegal,e.what()); }
    tx.metrics_.affected_connections=tasks.size();
    if(!tasks.empty()) {
        auto base=candidate.resources; // Occupancy of unaffected nets stays authoritative.
        tx.metrics_.copied_payload_bytes+=base.size()*sizeof(persistroute::Resource);
        assign_owners(base,owners(design_,candidate,affected));
        const auto route_begin=Clock::now();
        RoutingReply reply;
        try { reply=router_({design_,base,tasks,retain_branches?&retained:nullptr}); }
        catch(const std::exception& e) {
            tx.metrics_.routing_ns=elapsed(route_begin); return finish(Status::route_failed,e.what());
        }
        tx.metrics_.routing_ns=elapsed(route_begin);
        tx.metrics_.expanded=reply.expanded; tx.metrics_.edge_visits=reply.edge_visits;
        tx.metrics_.route_iterations=reply.iterations;
        tx.metrics_.kernel_searches=reply.kernel_searches;
        std::set<Id> requested;for(const auto& t:tasks)requested.insert(t.id);
        for(Id id:reply.feedback.connection_ids)
            if(!requested.count(id))return finish(Status::candidate_invalid,"feedback references an unrequested connection");
        for(Id id:reply.feedback.resource_ids)
            if(id>=candidate.resources.size())return finish(Status::candidate_invalid,"feedback resource out of range");
        tx.feedback_=std::move(reply.feedback);
        if(!reply.success) return finish(Status::route_failed,reply.detail);
        if(reply.tasks.size()!=tasks.size()) return finish(Status::candidate_invalid,"router omitted/added connections");
        std::map<Id,persistroute::Task> expected; for(const auto& t:tasks) expected.emplace(t.id,t);
        std::set<Id> seen;
        for(const auto& r:reply.tasks) {
            const auto f=expected.find(r.task.id);
            if(f==expected.end() || !seen.insert(r.task.id).second || !r.routed ||
               r.task.source!=f->second.source || r.task.sink!=f->second.sink || r.task.net_id!=f->second.net_id)
                return finish(Status::candidate_invalid,"router returned invalid task identity/status");
            auto& dst=candidate.routes[r.task.id];
            if(std::binary_search(tx.metrics_.retained_connections.begin(),tx.metrics_.retained_connections.end(),r.task.id)) {
                if(r.path!=dst.path)return finish(Status::candidate_invalid,"router changed a retained branch");
                continue;
            }
            dst.source=r.task.source; dst.sink=r.task.sink; dst.path=r.path;
            try { advance(dst.version); } catch(const std::exception& e) { return finish(Status::candidate_invalid,e.what()); }
        }
    }
    const auto validation_begin=Clock::now();
    try {
        auto before_use=owners(design_,*state_);
        auto after_use=owners(design_,candidate);
        assign_owners(candidate.resources,after_use);
        // PR private iteration costs/versions are scratch, not published. Bump
        // each net-tree resource once, including unchanged occupancy ownership.
        std::set<Id> touched;
        for(Id i=0;i<design_.connections.size();++i) if(affected.count(design_.connections[i].net)) {
            touched.insert(state_->routes[i].path.begin(),state_->routes[i].path.end());
            touched.insert(candidate.routes[i].path.begin(),candidate.routes[i].path.end());
        }
        for(Id node:touched) advance(candidate.resources[node].version);
        tx.metrics_.touched_resources=touched.size();
        for(Id node=0;node<before_use.size();++node)
            if(before_use[node]!=after_use[node] && !touched.count(node)) throw std::logic_error("untracked resource write");
        advance(candidate.revision);
        state_check(design_,candidate);
        std::string detail;
        if(validator_ && !validator_(design_,candidate,detail)) {
            tx.metrics_.validation_ns=elapsed(validation_begin); return finish(Status::candidate_invalid,detail);
        }
    } catch(const std::exception& e) {
        tx.metrics_.validation_ns=elapsed(validation_begin); return finish(Status::candidate_invalid,e.what());
    }
    tx.metrics_.validation_ns=elapsed(validation_begin);
    if(accept && !accept(design_,*state_,candidate)) return finish(Status::quality_rejected,"acceptance policy veto");
    return finish(Status::ready,"");
}

Status Engine::commit(Transaction& tx) {
    const auto begin=Clock::now();
    auto finish=[&](Status status) { tx.metrics_.commit_ns+=elapsed(begin); return status; };
    if(tx.origin_!=identity_) return finish(Status::foreign_transaction);
    if(tx.consumed_) return finish(Status::consumed);
    tx.consumed_=true;
    if(tx.status_!=Status::ready) return finish(tx.status_);
    if(tx.base_->timing_epoch!=state_->timing_epoch) return finish(tx.status_=Status::stale_timing);
    if(tx.base_!=state_ || tx.base_->revision!=state_->revision) return finish(tx.status_=Status::stale_state);
    // Allocation of the shared_ptr control block completes before publication.
    std::shared_ptr<const State> next(std::move(tx.candidate_));
    state_.swap(next);
    return finish(tx.status_=Status::committed);
}
void Engine::timing_barrier(std::uint64_t observed,const std::vector<std::uint16_t>& values) {
    if(observed!=state_->revision || values.size()!=design_.connections.size())
        throw std::invalid_argument("stale or incomplete timing snapshot");
    auto next=std::make_shared<State>(*state_);
    next->criticalities=values; next->timing_basis_revision=observed;
    advance(next->timing_epoch); advance(next->revision); state_=std::move(next);
}

persistroute::KernelBatchExecutor guarded_cmodel_executor(const Design& design,
    const std::vector<persistroute::Task>& input_tasks,Id pe_count) {
    if(!pe_count)throw std::invalid_argument("zero PR concurrency");
        std::uint64_t max_static_step=0;
        std::uint16_t max_criticality=0;
        for(const auto& task:input_tasks)max_criticality=std::max(max_criticality,task.criticality_q);
        for(const auto& edge:design.edges)max_static_step=std::max(max_static_step,
            std::uint64_t(edge.base_cost_q)+std::uint64_t(edge.delay_q)*max_criticality/65535U);
        return [=](const auto& nodes,const auto& edges,auto& resources,const auto& tasks,const auto& seeds,bool overuse) {
            // Upstream kernels saturate arithmetic. Reject a conservative
            // range bound before calling them; never accept a saturated run.
            std::uint64_t max_congestion=0;
            for(const auto& r:resources) {
                if(r.present_cost_q==65535 || r.history_cost_q==65535 || r.version>0xfffffff0U)
                    throw std::overflow_error("PR numeric guard: scratch cost/version reached reserved limit");
                const auto excess=std::max<std::int64_t>(0,std::int64_t(r.occupancy)+1-r.capacity);
                max_congestion=std::max(max_congestion,std::uint64_t(r.history_cost_q)+std::uint64_t(r.present_cost_q)*excess);
            }
            std::uint64_t max_seed=0,hop_bound=0;
            for(const auto& group:seeds)for(const auto& seed:group)max_seed=std::max(max_seed,std::uint64_t(seed.cost_q));
            for(const auto& task:tasks)hop_bound=std::max(hop_bound,std::min<std::uint64_t>(task.max_hops,nodes.size()));
            if(max_seed+(max_static_step+max_congestion)*hop_bound>=0xffffffffULL)
                throw std::overflow_error("PR numeric guard: conservative uint32 path-cost bound exceeded");
            return persistroute::execute_hbm_cmodel_batch(nodes,edges,resources,tasks,seeds,overuse,pe_count);
        };
}

Router pr_cmodel_router(persistroute::PathfinderConfig config,Id pe_count,Id width) {
    if(!pe_count || !width) throw std::invalid_argument("zero PR concurrency");
    return [=](const RoutingRequest& req) {
        if(req.retained && !req.retained->empty())throw std::invalid_argument("PR whole-net adapter cannot retain branches");
        const auto exec=guarded_cmodel_executor(req.design,req.tasks,pe_count);
        auto result=persistroute::route_accelerated_pathfinder(req.design.nodes,req.design.edges,
            req.base_resources,req.tasks,exec,config,width);
        RoutingReply reply;
        reply.success=result.routing.route_success && result.routing.legal;
        reply.tasks=std::move(result.routing.tasks);
        reply.expanded=result.routing.metrics.expanded; reply.edge_visits=result.routing.metrics.edge_visits;
        reply.iterations=result.routing.metrics.iterations;
        reply.kernel_searches=result.routing.metrics.searches;
        if(!reply.success) {
            reply.detail="PR did not produce a complete capacity-legal routing";
            reply.feedback.kind=FeedbackKind::routing;
            std::set<Id> overused;
            for(Id node=0;node<result.routing.resources.size();++node)
                if(result.routing.resources[node].occupancy>result.routing.resources[node].capacity)overused.insert(node);
            reply.feedback.resource_ids.assign(overused.begin(),overused.end());
            for(const auto& task:reply.tasks) {
                bool implicated=!task.routed;
                for(Id node:task.path)implicated|=overused.count(node)!=0;
                if(implicated)reply.feedback.connection_ids.push_back(task.task.id);
            }
        }
        return reply;
    };
}

std::string semantic_digest(const State& s) {
    std::uint64_t h=14695981039346656037ULL;
    auto word=[&](std::uint64_t v) { for(unsigned b=0;b<8;++b) { h^=(v>>(8*b))&255U; h*=1099511628211ULL; } };
    word(s.revision); word(s.timing_epoch); word(s.timing_basis_revision);
    word(s.placement.size()); for(const auto& p:s.placement) {word(p.site);word(p.version);}
    word(s.site_versions.size()); for(auto v:s.site_versions) word(v);
    word(s.routes.size()); for(const auto& r:s.routes) { word(r.source);word(r.sink);word(r.version);word(r.path.size());for(auto n:r.path) word(n); }
    word(s.resources.size()); for(const auto& r:s.resources) {word(r.occupancy);word(r.capacity);word(r.owner);word(r.version);word(r.present_cost_q);word(r.history_cost_q);}
    word(s.criticalities.size()); for(auto v:s.criticalities) word(v);
    std::ostringstream out; out<<std::hex<<std::setfill('0')<<std::setw(16)<<h; return out.str();
}
std::uint64_t routed_wire_units(const Design& d,const State& s) {
    auto use=owners(d,s); std::uint64_t total=0;
    for(Id n=0;n<use.size();++n) total+=std::uint64_t(d.nodes[n].delay_class)*use[n].size();
    return total;
}
std::vector<Proposal> propose_moves(const Design& d,const State& s,std::size_t limit) {
    std::vector<Proposal> result;if(limit==0)return result;
    // A deliberately simple component baseline: rank legal move/swap candidates
    // by affected-net HPWL delta. This is not a TP research contribution.
    std::map<Id,std::set<Id>> net_instances;
    std::vector<std::set<Id>> incidence(d.instances.size());
    for(const auto& c:d.connections) {
        net_instances[c.net].insert(c.source_instance);net_instances[c.net].insert(c.sink_instance);
        incidence[c.source_instance].insert(c.net);incidence[c.sink_instance].insert(c.net);
    }
    auto hpwl=[&](Id net,const State& state) {
        std::int64_t xmin=std::numeric_limits<std::int32_t>::max(),ymin=xmin;
        std::int64_t xmax=std::numeric_limits<std::int32_t>::min(),ymax=xmax;
        for(Id inst:net_instances.at(net)) {
            const auto& site=d.sites[state.placement[inst].site];
            xmin=std::min(xmin,std::int64_t(site.x));xmax=std::max(xmax,std::int64_t(site.x));
            ymin=std::min(ymin,std::int64_t(site.y));ymax=std::max(ymax,std::int64_t(site.y));
        }
        return xmax-xmin+ymax-ymin;
    };
    std::map<Id,std::int64_t> initial_cost;
    for(const auto& item:net_instances)initial_cost[item.first]=hpwl(item.first,s);
    struct Ranked {std::int64_t delta,distance;Proposal proposal;};
    std::vector<Ranked> ranked;
    std::set<std::vector<std::pair<Id,Id>>> emitted;
    State trial;trial.placement=s.placement;trial.site_versions=s.site_versions;
    for(Id i=0;i<d.instances.size();++i) {
        if(d.instances[i].fixed) continue;
        auto sites=d.instances[i].allowed_sites;
        const auto& origin=d.sites.at(s.placement[i].site);
        auto distance=[&](Id site) {
            const auto& target=d.sites.at(site);
            return std::abs(std::int64_t(origin.x)-target.x)+std::abs(std::int64_t(origin.y)-target.y)+
                std::abs(std::int64_t(origin.subtile)-target.subtile);
        };
        std::sort(sites.begin(),sites.end(),[&](Id a,Id b){return std::make_pair(distance(a),a)<std::make_pair(distance(b),b);});
        for(Id site:sites) {
            if(site==s.placement[i].site) continue;
            Proposal p; p.id=result.size();
            p.moves.push_back({i,s.placement[i].site,site,s.placement[i].version});
            for(Id j=0;j<s.placement.size();++j) if(j!=i && s.placement[j].site==site)
                p.moves.push_back({j,site,s.placement[i].site,s.placement[j].version});
            std::vector<std::pair<Id,Id>> key;
            for(const auto& m:p.moves)key.emplace_back(m.instance,m.new_site);
            std::sort(key.begin(),key.end());if(!emitted.insert(key).second)continue;
            bool fixed=false;trial.placement=s.placement;
            for(const auto& m:p.moves) { fixed|=d.instances[m.instance].fixed; trial.placement[m.instance].site=m.new_site; }
            if(fixed) continue;
            try { placement_check(d,trial); } catch(const std::exception&) {continue;}
            std::set<Id> affected;
            for(const auto& m:p.moves)affected.insert(incidence[m.instance].begin(),incidence[m.instance].end());
            std::int64_t delta=0;for(Id net:affected)delta+=hpwl(net,trial)-initial_cost.at(net);
            p.id=ranked.size();ranked.push_back({delta,distance(site),std::move(p)});
        }
    }
    std::sort(ranked.begin(),ranked.end(),[](const Ranked& a,const Ranked& b) {
        return std::make_tuple(a.delta,a.distance,a.proposal.id)<std::make_tuple(b.delta,b.distance,b.proposal.id);
    });
    for(std::size_t i=0;i<std::min(limit,ranked.size());++i) {
        ranked[i].proposal.id=i;result.push_back(std::move(ranked[i].proposal));
    }
    return result;
}
ControllerResult run_proposal(Engine& engine,const Proposal& initial,std::uint32_t budget,
                             const Repair& repair,const Sketch& sketch,const Acceptance& accept) {
    ControllerResult result;
    std::vector<Proposal> pending{initial}; std::set<std::string> visited;
    std::uint32_t repairs=0;
    for(std::size_t i=0;i<pending.size();++i) {
        const auto p=pending[i]; // repair appends to pending
        std::vector<std::tuple<Id,Id,Id,std::uint32_t>> keys;
        for(const auto& m:p.moves) keys.emplace_back(m.instance,m.old_site,m.new_site,m.observed_version);
        std::sort(keys.begin(),keys.end()); std::ostringstream key;
        for(const auto& k:keys) key<<std::get<0>(k)<<':'<<std::get<1>(k)<<':'<<std::get<2>(k)<<':'<<std::get<3>(k)<<';';
        if(!visited.insert(key.str()).second) continue;
        if(!result.attempts.empty()) { if(repairs==budget) break; ++repairs; }
        Attempt a; a.proposal_id=p.id; a.repair_index=repairs; a.before=semantic_digest(engine.state());
        auto tx=engine.prepare(p,sketch,accept); a.status=engine.commit(tx); a.metrics=tx.metrics(); a.detail=tx.detail();
        a.after=semantic_digest(engine.state()); result.attempts.push_back(a);
        if(a.status==Status::committed) {result.accepted=true;break;}
        if(a.before!=a.after) throw std::logic_error("rejected transaction changed authoritative state");
        if(repair && repairs<budget) {
            auto candidates=repair(engine.design(),engine.state(),p,a.status);
            const auto remaining=budget-repairs;
            if(candidates.size()>remaining) candidates.resize(remaining);
            pending.insert(pending.end(),candidates.begin(),candidates.end());
        }
    }
    return result;
}
} // namespace fusionpar::joint
