#include "rr_backend.hpp"
#include "speculative_backend.hpp"
#include "external_timing.hpp"
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <type_traits>

template<class T> std::vector<T> read(const std::string& path) {
    static_assert(std::is_trivially_copyable<T>::value, "binary ABI only");
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    if (!in || in.tellg() < 0 || std::uint64_t(in.tellg()) % sizeof(T)) throw std::runtime_error("invalid " + path);
    std::vector<T> out(std::uint64_t(in.tellg()) / sizeof(T)); in.seekg(0);
    if (!out.empty()) in.read(reinterpret_cast<char*>(out.data()), out.size() * sizeof(T));
    if (!in) throw std::runtime_error("read failed " + path);
    return out;
}
unsigned env(const char* name, unsigned value) {
    const auto* s = std::getenv(name); if (!s) return value;
    std::size_t used; const auto result = std::stoul(s, &used);
    if (s[used] || result > 0xffffffffULL) throw std::runtime_error(std::string("invalid ") + name);
    return result;
}
int main(int argc, char** argv) {
    try {
        using namespace persistroute;
        static_assert(sizeof(Node)==8 && sizeof(Edge)==8 && sizeof(Resource)==16 && sizeof(Task)==32 && sizeof(dieroute::RRBox)==8, "ABI");
        if (argc != 5) throw std::runtime_error("usage: dieroute_rr <PR-input-prefix> <topology-prefix> <output-prefix> <hierarchical|downstream|downstream_bounded|flat>");
        const std::string input=argv[1], topology=argv[2], output=argv[3], mode=argv[4];
        if (mode != "hierarchical" && mode != "flat" && mode != "downstream" && mode != "downstream_bounded") throw std::runtime_error("invalid mode");
        const auto begin=std::chrono::steady_clock::now();
        auto nodes=read<Node>(input+".nodes"); auto edges=read<Edge>(input+".edges");
        auto resources=read<Resource>(input+".resources"); auto tasks=read<Task>(input+".tasks");
        dieroute::RRBackendConfig cfg; cfg.hierarchical=mode!="flat";
        cfg.downstream_cost=mode=="downstream" || mode=="downstream_bounded";cfg.bound_downstream=mode=="downstream_bounded";
        cfg.repair_attempts=env("DIEROUTE_REPAIR_ATTEMPTS",8); cfg.geometry_weight=env("DIEROUTE_GEOMETRY_WEIGHT",64);
        const auto cost_model=env("DIEROUTE_VPR_STYLE_COST",0);
        if(cost_model>1) throw std::runtime_error("DIEROUTE_VPR_STYLE_COST must be 0 or 1");
        cfg.vpr_style_cost=cost_model;
        const auto edge_mode=env("DIEROUTE_EDGE_IDENTITY",0);
        if(edge_mode>1)throw std::runtime_error("DIEROUTE_EDGE_IDENTITY must be 0 or 1");
        cfg.edge_identity=edge_mode;
        const std::uint16_t criticality_cap=cfg.vpr_style_cost?64880:65535;
        for(auto& task:tasks) task.criticality_q=std::min(task.criticality_q,criticality_cap);
        std::vector<std::uint16_t> membership, edge_die;
        const bool native_membership = std::ifstream(topology+".node_membership").good() ||
                                       std::ifstream(topology+".edge_die").good();
        if(native_membership) {
            membership=read<std::uint16_t>(topology+".node_membership");
            edge_die=read<std::uint16_t>(topology+".edge_die");
            if(membership.empty() || edge_die.empty()) throw std::runtime_error("empty native membership/PIP sidecars");
        }
        std::vector<std::uint32_t> edge_refs;
        if(cfg.edge_identity && native_membership){
            edge_refs=read<std::uint32_t>(topology+".edge_ref");
            if(edge_refs.size()!=edges.size() || std::set<std::uint32_t>(edge_refs.begin(),edge_refs.end()).size()!=edge_refs.size())
                throw std::runtime_error("native edge_ref must have one unique PIP ID/direction key per CSR edge");
        }
        dieroute::RoutingPolicyPtr policy;
        if(std::ifstream(topology+".node_protection").good() || std::ifstream(topology+".terminal_net").good() || std::ifstream(topology+".edge_protection").good()){
            auto value=std::make_shared<dieroute::RoutingPolicy>();
            value->node_protection=read<std::uint8_t>(topology+".node_protection");
            value->terminal_net=read<std::uint32_t>(topology+".terminal_net");
            value->edge_protection=read<std::uint8_t>(topology+".edge_protection");
            value->validate(nodes.size(),edges.size());
            if(!value->active())throw std::runtime_error("empty routing policy sidecars");
            policy=value;
        }
        const auto workers=env("DIEROUTE_SPECULATIVE_WORKERS",0);
        const auto shadow_sync=env("DIEROUTE_SHADOW_SYNC_WINDOWS",1);
        if(workers>32 || !shadow_sync) throw std::runtime_error("invalid speculative worker/shadow configuration");
        auto owners=read<std::uint16_t>(topology+".node_die");auto boxes=read<dieroute::RRBox>(topology+".node_box");
        std::unique_ptr<dieroute::RRBackend> backend;
        std::unique_ptr<dieroute::SpeculativeBackend> speculative;
        if(workers) speculative=std::make_unique<dieroute::SpeculativeBackend>(nodes,edges,owners,boxes,cfg,membership,edge_die,workers,shadow_sync,policy);
        else backend=std::make_unique<dieroute::RRBackend>(nodes,edges,owners,boxes,cfg,membership,edge_die,policy);
        PathfinderConfig controller;
        controller.max_iterations=env("DIEROUTE_MAX_ITERATIONS",30);
        controller.min_timing_iterations=env("DIEROUTE_MIN_TIMING_ITERATIONS",1);
        controller.timing_update_period=env("DIEROUTE_TIMING_UPDATE_PERIOD",1);
        const auto tree_timing_weight=env("DIEROUTE_TREE_TIMING_WEIGHT_Q",0);
        if(tree_timing_weight>65535U) throw std::runtime_error("DIEROUTE_TREE_TIMING_WEIGHT_Q exceeds u16");
        controller.route_tree_timing_weight_q=static_cast<std::uint16_t>(tree_timing_weight);
        const auto issue=env("DIEROUTE_ISSUE_WIDTH",4);
        const auto cost_bits=env("DIEROUTE_COST_BITS",16);
        if(cost_bits!=16 && cost_bits!=64) throw std::runtime_error("DIEROUTE_COST_BITS must be 16 or 64");
        if(cfg.edge_identity && cost_bits!=64)throw std::runtime_error("edge identity requires DIEROUTE_COST_BITS=64");
        TimingAnalyzer timing;
        const auto* timing_command=std::getenv("PERSISTROUTE_TIMING_COMMAND");
        if(timing_command && *timing_command) {
            if(cfg.edge_identity)throw std::runtime_error("legacy external timing accepts node paths only; edge mode requires a calibrated edge-aware adapter");
            const auto native_timing=make_external_timing_analyzer(timing_command,output);
            timing=[native_timing,criticality_cap](auto iteration,const auto& n,const auto& e,const auto& t) {
                auto update=native_timing(iteration,n,e,t);
                for(auto& connection:update.connections) connection.criticality_q=std::min(connection.criticality_q,criticality_cap);
                return update;
            };
        }
        std::uint32_t checked_epoch=INVALID_RESOURCE;
        KernelBatchExecutor executor=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over) {
            if(!t.empty() && t.front().epoch!=checked_epoch) {
                for(const auto& state:r)if(state.present_cost_q==65535 || state.history_cost_q==65535)
                    throw std::overflow_error("PR fixed-point congestion saturation: abort; widen cost state before accepting this run");
                checked_epoch=t.front().epoch;
            }
            return speculative?speculative->execute(n,e,r,t,s,over):backend->execute(n,e,r,t,s,over);
        };
        dieroute::WidePathfinderResult wide;
        AcceleratedPathfinderResult result;
        if(cost_bits==64) {
            dieroute::WideBatchExecutor wide_executor=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over,const auto& costs) {
                return speculative?speculative->execute(n,e,r,t,s,over,&costs):backend->execute(n,e,r,t,s,over,&costs);
            };
            if(cfg.edge_identity){
                dieroute::EdgeBatchExecutor edge_executor=[&](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over,const auto& costs){
                    return speculative?speculative->execute_edges(n,e,r,t,s,over,&costs):backend->execute_edges(n,e,r,t,s,over,&costs);};
                wide=dieroute::route_wide_pathfinder_edges(nodes,edges,resources,tasks,edge_executor,controller,issue,{},policy);
            }else wide=dieroute::route_wide_pathfinder(nodes,edges,resources,tasks,wide_executor,controller,issue,timing);
            result=std::move(wide.result);
        } else result=route_accelerated_pathfinder(nodes,edges,resources,tasks,executor,controller,issue,timing);
        const auto& routing=result.routing;
        if(cfg.edge_identity){
            std::ofstream edge_paths(output+".path_edges.csv"),edge_trees(output+".tree_edges.csv");
            edge_paths<<"task_id,path_index,parent,child,edge_id,native_pip_key\n";
            for(std::size_t i=0;i<routing.tasks.size();++i){const auto& task=routing.tasks[i];auto parent=task.task.source;
                for(std::size_t j=0;j<task.path.size();++j){const auto id=wide.task_edges.at(i).at(j);
                    edge_paths<<task.task.id<<','<<j<<','<<parent<<','<<task.path[j]<<','<<id<<',';
                    if(native_membership)edge_paths<<edge_refs.at(id);
                    edge_paths<<'\n';parent=task.path[j];}}
            edge_trees<<"net_id,parent,child,edge_id,native_pip_key\n";
            for(const auto& e:wide.tree_edges){edge_trees<<e.net_id<<','<<e.parent<<','<<e.child<<','<<e.edge<<',';
                if(native_membership)edge_trees<<edge_refs.at(e.edge);
                edge_trees<<'\n';}
            edge_paths.close();edge_trees.close();
            if(!edge_paths||!edge_trees)throw std::runtime_error("edge identity output write failed");
        }
        std::ofstream paths(output+".paths.csv"),trees(output+".route_trees.csv"),iterations(output+".iterations.csv"),
            audits(output+".audit.csv"),binary(output+".resources",std::ios::binary),timing_log(output+".timing_iterations.csv"),
            cost_binary(output+".costs",std::ios::binary);
        paths<<"task_id,path_index,resource_id\n";
        for(const auto& t:routing.tasks)for(std::size_t i=0;i<t.path.size();++i) paths<<t.task.id<<','<<i<<','<<t.path[i]<<'\n';
        trees<<"net_id,source,parent,child\n";
        for(const auto& t:routing.route_trees)for(auto e:t.edges)trees<<t.net_id<<','<<t.source<<','<<e.parent<<','<<e.child<<'\n';
        iterations<<"iteration,routed_nets,failed_connections,overused_resources,present_factor_q\n";
        for(auto i:routing.iteration_log)iterations<<i.iteration<<','<<i.routed_nets<<','<<i.failed_connections<<','<<i.overused_resources<<','
            <<(cost_bits==64?wide.present_factors.at(i.iteration):i.present_factor_q)<<'\n';
        audits<<"iteration,issue_width,committed,failed,resource_hash,route_hash\n";
        for(auto a:result.audit)audits<<a.iteration<<','<<a.issue_width<<','<<a.committed<<','<<a.failed<<','<<a.resource_hash<<','<<a.route_hash<<'\n';
        timing_log<<"iteration,updated_connections,min_criticality_q,max_criticality_q,critical_path_delay_ps\n";
        for(auto a:routing.timing_log)timing_log<<a.iteration<<','<<a.updated_connections<<','<<a.min_criticality_q<<','<<a.max_criticality_q<<','<<a.critical_path_delay_ps<<'\n';
        std::ofstream transactions(output+".transactions.csv");
        transactions<<"window,task_id,epoch,priority,initial_status,final_status,initial_reads,final_reads,initial_read_hash,replay_read_hash,path_hash,replayed\n";
        const char* statuses[]={"committed","stale","unreachable","capacity","invalid","overflow"};
        if(speculative)for(const auto& row:speculative->trace())
            transactions<<row.window<<','<<row.task<<','<<row.epoch<<','<<row.priority<<','
                <<statuses[static_cast<unsigned>(row.initial_status)]<<','<<statuses[static_cast<unsigned>(row.final_status)]<<','
                <<row.initial_reads<<','<<row.final_reads<<','<<row.initial_read_hash<<','<<row.replay_read_hash<<','<<row.path_hash<<','<<row.replayed<<'\n';
        transactions.close();if(!transactions)throw std::runtime_error("transaction trace write failed");
        binary.write(reinterpret_cast<const char*>(routing.resources.data()),routing.resources.size()*sizeof(Resource));
        // Explicit little-endian records avoid native struct padding/endian ABI.
        std::uint64_t maximum_present=0,maximum_history=0;
        for(std::size_t i=0;i<routing.resources.size();++i) {
            const auto c=cost_bits==64?wide.costs.at(i):dieroute::WideCost{routing.resources[i].present_cost_q,routing.resources[i].history_cost_q};
            maximum_present=std::max(maximum_present,c.present_q);maximum_history=std::max(maximum_history,c.history_q);
            for(auto word:{c.present_q,c.history_q})for(unsigned byte=0;byte<8;++byte)cost_binary.put(static_cast<char>((word>>(8*byte))&255U));
        }
        paths.close();trees.close();iterations.close();audits.close();binary.close();timing_log.close();cost_binary.close();
        if(!paths||!trees||!iterations||!audits||!binary||!timing_log||!cost_binary)throw std::runtime_error("output write failed");
        const auto& m=speculative?speculative->metrics():backend->metrics();
        const auto sm=speculative?speculative->speculative_metrics():dieroute::SpeculativeMetrics{};
        const auto shadows=speculative?speculative->shadow_metrics():dieroute::ShadowMetrics{};
        const auto end=std::chrono::steady_clock::now();
        std::ofstream report(output+".json");
        report<<"{\"schema\":\"dieroute.rr_golden.v1\",\"mode\":\""<<mode<<"\",\"legal\":"<<(routing.legal?"true":"false")
            <<",\"edge_identity\":"<<(cfg.edge_identity?"true":"false")
            <<",\"immutable_admission\":"<<(policy?"true":"false")
            <<",\"protected_nodes\":"<<(policy?std::count_if(policy->node_protection.begin(),policy->node_protection.end(),[](auto v){return v!=0;}):0)
            <<",\"exclusive_terminal_nodes\":"<<(policy?std::count_if(policy->terminal_net.begin(),policy->terminal_net.end(),[](auto v){return v!=INVALID_RESOURCE;}):0)
            <<",\"forbidden_edges\":"<<(policy?std::count_if(policy->edge_protection.begin(),policy->edge_protection.end(),[](auto v){return v!=0;}):0)
            <<",\"route_hash_schema\":\""<<(cfg.edge_identity?"task_nodes_and_csr_edges_v1":"task_nodes_v1")<<"\""
            <<",\"native_edge_key_encoding\":\""<<(cfg.edge_identity&&native_membership?"catalog_pip_id_shift1_or_direction_u32":"none")<<"\""
            <<",\"topology_model\":\""<<(native_membership?"native_pip_membership":"single_die_nodes")<<"\""
            <<",\"execution\":\""<<(workers?"cpu_speculative_reference":"serial_cpp_reference")<<"\",\"board_result\":false,\"iterations\":"<<routing.metrics.iterations
            <<",\"route_tree_timing_weight_q\":"<<controller.route_tree_timing_weight_q
            <<",\"cost_model\":\""<<(cfg.vpr_style_cost?"vpr_style":"additive")<<"\",\"criticality_cap_q\":"<<criticality_cap
            <<",\"cost_state_bits\":"<<cost_bits<<",\"cost_encoding\":\"little_endian_u64_present_history\""
            <<",\"resource_encoding\":\""<<(cost_bits==64?"pr16_zero_cost_fields_plus_cost64_v1":"pr16_v1")<<"\""
            <<",\"maximum_present_q\":"<<maximum_present<<",\"maximum_history_q\":"<<maximum_history
            <<",\"tasks\":"<<tasks.size()<<",\"overused_resources\":"<<routing.metrics.overused_resources
            <<",\"expanded\":"<<routing.metrics.expanded<<",\"edge_visits\":"<<routing.metrics.edge_visits
            <<",\"planned\":"<<m.planned<<",\"local_searches\":"<<m.local_searches<<",\"flat_searches\":"<<m.flat_searches
            <<",\"reserved_resources\":"<<m.reserved_resources<<",\"aborted_reservations\":"<<m.aborted_reservations
            <<",\"committed_corridors\":"<<m.committed_corridors<<",\"repairs\":"<<m.repairs<<",\"fallbacks\":"<<m.fallbacks
            <<",\"committed_crossings\":"<<m.committed_crossings<<",\"overcapacity_reservations\":"<<m.overcapacity_reservations
            <<",\"structurally_pruned_portals\":"<<m.structurally_pruned_portals
            <<",\"downstream_searches\":"<<m.downstream_searches<<",\"downstream_expanded\":"<<m.downstream_expanded
            <<",\"downstream_edge_visits\":"<<m.downstream_edge_visits
            <<",\"downstream_cutoffs\":"<<m.downstream_cutoffs
            <<",\"speculative_workers\":"<<workers<<",\"shadow_sync_windows\":"<<shadow_sync
            <<",\"speculative_windows\":"<<sm.windows<<",\"speculative_proposals\":"<<sm.proposals
            <<",\"speculative_replays\":"<<sm.replays<<",\"speculative_conflicts\":"<<sm.conflicts
            <<",\"speculative_read_entries\":"<<sm.read_entries<<",\"remote_shadow_reads\":"<<sm.remote_shadow_reads
            <<",\"maximum_window_tasks\":"<<sm.maximum_window_tasks
            <<",\"shadow_messages\":"<<shadows.published<<",\"shadow_summary_payload_bytes\":"<<shadows.payload_bytes
            <<",\"wall_ms\":"<<std::chrono::duration<double,std::milli>(end-begin).count()<<"}\n";
        report.close();if(!report)throw std::runtime_error("report write failed");
        std::cout<<"legal="<<routing.legal<<" iterations="<<routing.metrics.iterations<<" fallbacks="<<m.fallbacks<<'\n';
        return routing.legal?0:3;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
