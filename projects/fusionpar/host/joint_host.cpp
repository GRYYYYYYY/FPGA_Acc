#include "joint_io.hpp"

#include <chrono>
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <cmath>
#include <set>
#include <stdexcept>
#include <tuple>
#include <fcntl.h>
#include <sys/wait.h>
#include <unistd.h>

using namespace fusionpar::joint;
namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
std::uint64_t ns(Clock::time_point start) {return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count();}
int validate_process(const fs::path& script,const fs::path& bundle,const fs::path& state,const fs::path& work) {
    auto pid=fork();if(pid<0)throw std::runtime_error("fork failed");
    if(pid==0) {
        int fd=open((work/"adapter.log").c_str(),O_CREAT|O_WRONLY|O_TRUNC,0644);
        if(fd<0)_exit(126);dup2(fd,STDOUT_FILENO);dup2(fd,STDERR_FILENO);close(fd);
        execlp("python3","python3",script.c_str(),bundle.c_str(),state.c_str(),work.c_str(),static_cast<char*>(nullptr));_exit(127);
    }
    int status=0;while(waitpid(pid,&status,0)<0) {if(errno!=EINTR)throw std::runtime_error("waitpid failed");}
    return WIFEXITED(status)?WEXITSTATUS(status):128;
}
int main(int argc,char** argv) {
    const auto begin=Clock::now();
    try {
        if(argc!=6 && argc!=7)throw std::invalid_argument("usage: fusionpar_host BUNDLE OUTPUT MODE ATTEMPTS VALIDATOR.py|--internal-only [TREE_TIMING_WEIGHT_Q]");
        fs::path bundle=fs::absolute(argv[1]),out=fs::absolute(argv[2]);std::string mode=argv[3];
        if(mode!="interleaved"&&mode!="interleaved_repair"&&mode!="sequential_shared"&&mode!="sequential"&&mode!="protocol_probe"&&mode!="interleaved_placement_repair"&&mode!="interleaved_tree_control"&&mode!="interleaved_tree_reuse"&&mode!="sequential_tree_reuse"&&mode!="sequential_shared_tree_reuse"&&mode!="route_only"&&mode!="interleaved_tree_feedback")throw std::invalid_argument("unknown mode");
        const bool cold=mode=="sequential" || mode=="sequential_tree_reuse";
        const bool batch_reuse=mode=="sequential_tree_reuse" || mode=="sequential_shared_tree_reuse";
        const bool budget_feedback=mode=="interleaved_tree_feedback";
        const bool placement_feedback=mode=="interleaved_placement_repair" || budget_feedback;
        const bool retain=mode=="interleaved_tree_reuse" || budget_feedback;
        std::string count_arg=argv[4];std::size_t parsed=0;auto count=std::stoul(count_arg,&parsed);
        if(parsed!=count_arg.size()||count>1000||count==0)throw std::invalid_argument("ATTEMPTS must be 1..1000");
        std::uint16_t tree_timing_weight=0;
        if(argc==7) {
            std::string value=argv[6];std::size_t consumed=0;auto weight=std::stoul(value,&consumed);
            if(consumed!=value.size() || weight>256 || value.empty() || value[0]=='-')
                throw std::invalid_argument("TREE_TIMING_WEIGHT_Q must be 0..256 (Q8)");
            tree_timing_weight=static_cast<std::uint16_t>(weight);
        }
        if(fs::exists(out))throw std::invalid_argument("output directory already exists");
        fs::create_directories(out);
        auto [design,initial]=read_bundle(bundle);auto load_ns=ns(begin);
        const bool native=std::string(argv[5])!="--internal-only";
        if((mode=="protocol_probe"||mode=="route_only")&&!native)throw std::invalid_argument("protocol_probe requires native validation");
        fs::path script=fs::absolute(argv[5]);std::uint64_t validation_index=0,native_ns=0;
        struct Quality {double cpd;std::uint64_t wire;};
        std::map<std::string,Quality> qualities;
        struct Timing {std::vector<std::uint16_t> values;std::vector<std::uint64_t> delays;std::uint64_t validation_index;};
        std::map<std::string,Timing> timings;
        Validator validator;
        if(native) validator=[&](const Design&,const State& state,std::string& detail) {
            auto start=Clock::now();auto work=out/("validation_"+std::to_string(validation_index++));fs::create_directories(work);
            write_state(state,work/"candidate.state");auto status=validate_process(script,bundle,work/"candidate.state",work);
            native_ns+=ns(start);detail="native validation exit="+std::to_string(status)+" directory="+work.string();
            if(status!=0)return false;
            std::ifstream quality(work/"quality.txt");Quality q{};std::string extra;
            if(!(quality>>q.cpd>>q.wire)||!std::isfinite(q.cpd)||q.cpd<=0||(quality>>extra))return false;
            const auto digest=semantic_digest(state);
            qualities[digest]=q;
            if(fs::exists(work/"timing.txt")) {
                std::ifstream input(work/"timing.txt");std::size_t count_values=0;
                if(!(input>>count_values)||count_values!=state.criticalities.size())return false;
                Timing timing;timing.validation_index=validation_index-1;
                for(std::size_t i=0;i<count_values;++i) {
                    std::uint32_t value=0;if(!(input>>value)||value>65535)return false;
                    timing.values.push_back(static_cast<std::uint16_t>(value));
                }
                if(input>>extra)return false;
                std::ifstream delays(work/"connection_delays.txt");std::size_t count_delays=0;
                if(!(delays>>count_delays)||count_delays!=count_values)return false;
                for(std::size_t i=0;i<count_delays;++i) {
                    std::uint64_t value=0;if(!(delays>>value))return false;timing.delays.push_back(value);
                }
                if(delays>>extra)return false;
                timings[digest]=std::move(timing);
            }
            return true;
        };
        auto quality_feedback=[&](const State& before,const State& candidate) {
            FailureFeedback feedback;
            auto old=timings.find(semantic_digest(before)),next=timings.find(semantic_digest(candidate));
            if(old!=timings.end()&&next!=timings.end()) {
                for(Id i=0;i<design.connections.size();++i)
                    if(next->second.delays.at(i)>old->second.delays.at(i))feedback.connection_ids.push_back(i);
                std::sort(feedback.connection_ids.begin(),feedback.connection_ids.end(),[&](Id a,Id b) {
                    const auto da=next->second.delays[a]-old->second.delays[a],db=next->second.delays[b]-old->second.delays[b];
                    if(before.criticalities[a]!=before.criticalities[b])return before.criticalities[a]>before.criticalities[b];
                    return da!=db?da>db:a<b;
                });
                if(!feedback.connection_ids.empty()){feedback.kind=FeedbackKind::native_delay;return feedback;}
            }
            // If timing feedback is unavailable or has no worsened connection,
            // use exact unique-net RR wire growth, not an inferred CPD cause.
            std::map<Id,std::set<Id>> old_nodes,new_nodes;
            for(Id i=0;i<design.connections.size();++i) {
                auto net=design.connections[i].net;
                old_nodes[net].insert(before.routes[i].path.begin(),before.routes[i].path.end());
                new_nodes[net].insert(candidate.routes[i].path.begin(),candidate.routes[i].path.end());
            }
            std::set<Id> grown;
            for(const auto& item:old_nodes) {
                std::uint64_t a=0,b=0;for(Id node:item.second)a+=design.nodes[node].delay_class;
                for(Id node:new_nodes[item.first])b+=design.nodes[node].delay_class;
                if(b>a)grown.insert(item.first);
            }
            for(Id i=0;i<design.connections.size();++i)if(grown.count(design.connections[i].net))feedback.connection_ids.push_back(i);
            if(!feedback.connection_ids.empty())feedback.kind=FeedbackKind::wire_growth;
            return feedback;
        };
        persistroute::PathfinderConfig config;config.max_iterations=30;
        config.route_tree_timing_weight_q=tree_timing_weight;
        const bool tree_mode=mode=="interleaved_tree_control" || retain || batch_reuse;
        auto router=tree_mode?retained_cmodel_router(config):pr_cmodel_router(config);
        Acceptance accept=[&](const Design& d,const State& before,const State& candidate) {
            // Correctness-only successful-commit exercise. This mode must never
            // enter the protected QoR/performance comparison population.
            if(mode=="protocol_probe"||mode=="route_only")return true;
            if(!native)return routed_wire_units(d,candidate)<routed_wire_units(d,before);
            const auto& base=qualities.at(semantic_digest(initial));
            const auto& old=qualities.at(semantic_digest(before));
            const auto& next=qualities.at(semantic_digest(candidate));
            // Frozen development policy: native CPD within +2% of the initial
            // legal solution, then strict lexicographic (WL, CPD) improvement.
            return next.cpd<=base.cpd*1.02 && next.wire<=base.wire*1.02 &&
                std::make_pair(next.wire,next.cpd)<std::make_pair(old.wire,old.cpd);
        };
        std::unique_ptr<Engine> engine;
        if(!cold)engine=std::make_unique<Engine>(design,initial,router,validator);
        std::ofstream timing_events(out/"timing.jsonl");timing_events.exceptions(std::ios::badbit|std::ios::failbit);
        auto sync_timing=[&]() {
            const auto before=semantic_digest(engine->state());const auto found=timings.find(before);
            if(found==timings.end())return;
            const auto basis=engine->state().revision;
            engine->timing_barrier(basis,found->second.values);
            const auto after=semantic_digest(engine->state());qualities[after]=qualities.at(before);
            timings[after]=found->second;
            timing_events<<"{\"schema\":\"FUSIONPAR_TIMING_BARRIER_V1\",\"before\":\""<<before<<"\",\"after\":\""<<after
                <<"\",\"basis_revision\":"<<basis<<",\"timing_epoch\":"<<engine->state().timing_epoch
                <<",\"validation_index\":"<<found->second.validation_index<<",\"connections\":"<<found->second.values.size()<<"}\n";
            timing_events.flush();
        };
        if(engine)sync_timing();
        std::ofstream events(out/"events.jsonl");events.exceptions(std::ios::badbit|std::ios::failbit);
        std::uint64_t commits=0,aborts=0,copied=0,routing_ns=0,prepare_ns=0,validation_ns=0,placement_repairs=0;
        auto record=[&](Transaction& tx,Status status,const std::string& before,const std::string& after,
                        const char* phase="primary",std::uint32_t repair_index=0,const FailureFeedback* trigger=nullptr) {
            const auto& m=tx.metrics();copied+=m.copied_payload_bytes;routing_ns+=m.routing_ns;prepare_ns+=m.prepare_ns;validation_ns+=m.validation_ns;
            commits+=status==Status::committed;aborts+=status!=Status::committed;
            events<<"{\"schema\":\"FUSIONPAR_EVENT_V1\",\"proposal\":"<<tx.proposal().id<<",\"status\":\""<<status_name(status)
                <<"\",\"before\":\""<<before<<"\",\"after\":\""<<after<<"\",\"affected_nets\":"<<m.affected_nets
                <<",\"affected_connections\":"<<m.affected_connections<<",\"touched_resources\":"<<m.touched_resources
                <<",\"route_iterations\":"<<m.route_iterations<<",\"copy_payload_bytes\":"<<m.copied_payload_bytes
                <<",\"snapshot_ns\":"<<m.snapshot_ns<<",\"routing_ns\":"<<m.routing_ns<<",\"validation_ns\":"<<m.validation_ns
                <<",\"prepare_ns\":"<<m.prepare_ns<<",\"commit_ns\":"<<m.commit_ns<<",\"expanded\":"<<m.expanded
                <<",\"candidate_digest\":\""<<(tx.candidate()?semantic_digest(*tx.candidate()):(status==Status::committed?after:""))
                <<"\",\"phase\":\""<<phase<<"\",\"repair_index\":"<<repair_index<<",\"moves\":[";
            bool first=true;for(const auto& move:tx.proposal().moves) {
                if(!first)events<<',';first=false;
                events<<'['<<move.instance<<','<<move.old_site<<','<<move.new_site<<','<<move.observed_version<<']';
            }
            const auto& fb=trigger?*trigger:tx.feedback();
            events<<"],\"feedback_kind\":\""<<feedback_name(fb.kind)<<"\",\"feedback_connections\":[";
            first=true;for(Id id:fb.connection_ids){if(!first)events<<',';first=false;events<<id;}
            events<<"],\"feedback_resources\":[";
            first=true;for(Id id:fb.resource_ids){if(!first)events<<',';first=false;events<<id;}
            events<<"],\"retained_connections\":[";
            first=true;for(Id id:m.retained_connections){if(!first)events<<',';first=false;events<<id;}
            events<<"],\"kernel_searches\":"<<m.kernel_searches<<"}\n";
            events.flush();
        };
        auto proposals=mode=="route_only"?std::vector<Proposal>{}:propose_moves(design,initial,count);
        if(proposals.empty()&&mode!="route_only")throw std::runtime_error("no legal proposal");
        State final;
        if(mode=="route_only") {
            auto before=semantic_digest(engine->state());auto tx=engine->prepare_routing(accept);auto status=engine->commit(tx);
            record(tx,status,before,semantic_digest(engine->state()),"routing_epoch");
            if(status==Status::committed)sync_timing();
            final=engine->state();
        } else if(mode=="interleaved"||mode=="interleaved_repair"||mode=="protocol_probe"||placement_feedback||mode=="interleaved_tree_control"||retain) {
            std::set<std::vector<Id>> tried;
            for(std::size_t step=0;step<count;++step) {
                // Recompute candidates after every commit. Avoid retrying an
                // identical complete placement, even after a rejected route.
                auto pool=propose_moves(design,engine->state(),count*4+1);
                Proposal p;bool found=false;
                for(auto candidate:pool) {
                    std::vector<Id> layout;for(const auto& pos:engine->state().placement)layout.push_back(pos.site);
                    for(const auto& move:candidate.moves)layout[move.instance]=move.new_site;
                    if(tried.insert(layout).second){p=std::move(candidate);found=true;break;}
                }
                if(!found)break;
                p.id=step;
                auto before=semantic_digest(engine->state());auto tx=engine->prepare(p,{},accept,false,retain);auto status=engine->commit(tx);
                auto feedback=tx.feedback();
                if(placement_feedback && status==Status::quality_rejected && tx.candidate())
                    feedback=quality_feedback(engine->state(),*tx.candidate());
                record(tx,status,before,semantic_digest(engine->state()),"primary",0,&feedback);
                if(status==Status::committed)sync_timing();
                if(placement_feedback && (!budget_feedback || step+1<count) && (status==Status::route_failed || status==Status::quality_rejected)) {
                    const auto repairs=propose_repairs(design,engine->state(),p,status,feedback,2);
                    std::uint32_t repair_index=0;
                    for(const auto& alternative:repairs) {
                        // Feedback changes which candidate consumes the next
                        // evaluation slot; it never adds slots to this mode.
                        if(budget_feedback && step+1>=count)break;
                        std::vector<Id> layout;for(const auto& pos:engine->state().placement)layout.push_back(pos.site);
                        for(const auto& move:alternative.moves)layout[move.instance]=move.new_site;
                        if(!tried.insert(layout).second)continue;
                        if(budget_feedback)++step;
                        ++repair_index;++placement_repairs;
                        auto retry=engine->prepare(alternative,{},accept,false,retain);auto repaired=engine->commit(retry);
                        record(retry,repaired,before,semantic_digest(engine->state()),"placement_repair",repair_index,&feedback);
                        if(repaired==Status::committed){sync_timing();break;}
                    }
                }
                if(mode=="interleaved_repair"&&status==Status::route_failed) {
                    // One bounded global-routing repair: preserve the proposal,
                    // release all net trees in a private copy, then re-route.
                    auto retry=engine->prepare(p,{},accept,true);auto repaired=engine->commit(retry);
                    record(retry,repaired,before,semantic_digest(engine->state()),"global_route_repair",1);
                    if(repaired==Status::committed)sync_timing();
                }
            }
            final=engine->state();
        } else {
            // Stage a deterministic non-overlapping legal move batch. The tree
            // reuse control uses the same affected-net/retained-branch policy
            // as interleaved reuse; original sequential modes reroute all nets.
            Proposal batch;std::set<Id> instances,sites;
            for(const auto& p:proposals) {
                bool overlap=false;for(const auto& m:p.moves)overlap|=instances.count(m.instance)||sites.count(m.old_site)||sites.count(m.new_site);
                if(overlap)continue;
                for(const auto& m:p.moves){instances.insert(m.instance);sites.insert(m.old_site);sites.insert(m.new_site);batch.moves.push_back(m);}
            }
            if(cold) {
                // Actual reload/reconstruction is timed; shared mode keeps the
                // loaded design. Same initial native validation in both modes.
                auto reloaded=read_bundle(bundle);
                engine=std::make_unique<Engine>(std::move(reloaded.first),std::move(reloaded.second),router,validator);
                sync_timing();
            }
            auto before=semantic_digest(engine->state());auto tx=engine->prepare(batch,{},accept,!batch_reuse,batch_reuse);auto status=engine->commit(tx);
            record(tx,status,before,semantic_digest(engine->state()));
            if(status==Status::committed)sync_timing();
            final=engine->state();
        }
        write_state(final,out/"final.state");
        std::ofstream summary(out/"summary.json");summary.exceptions(std::ios::badbit|std::ios::failbit);
        summary<<"{\"schema\":\"FUSIONPAR_RUN_V1\",\"mode\":\""<<mode<<"\",\"native_validation\":"<<(native?"true":"false")
            <<",\"proposals\":"<<proposals.size()<<",\"commits\":"<<commits<<",\"aborts\":"<<aborts<<",\"copy_payload_bytes\":"<<copied
            <<",\"load_ns\":"<<load_ns<<",\"routing_ns\":"<<routing_ns<<",\"prepare_ns\":"<<prepare_ns<<",\"validation_ns\":"<<validation_ns
            <<",\"native_ns\":"<<native_ns<<",\"wall_ns\":"<<ns(begin)<<",\"semantic_digest\":\""<<semantic_digest(final)
            <<"\",\"wire_units\":"<<routed_wire_units(design,final)<<",\"timing_epoch\":"<<final.timing_epoch
            <<",\"placement_repairs\":"<<placement_repairs
            <<",\"evaluation_budget\":"<<(retain?count:0)<<",\"evaluations\":"<<(commits+aborts)
            <<",\"route_tree_timing_weight_q\":"<<tree_timing_weight
            <<",\"acceptance\":\""<<(mode=="protocol_probe"?"native_legality_only_PROTOCOL_TEST":mode=="route_only"?"native_legality_only_FIXED_PLACEMENT_PR_BASELINE":"strict_WL_CPD_lexicographic_with_initial_CPD_2pct_guard")<<"\"}\n";
        std::cout<<"fusionpar_host: commits="<<commits<<" aborts="<<aborts<<" output="<<out<<'\n';return 0;
    } catch(const std::exception& e){std::cerr<<"fusionpar_host: "<<e.what()<<'\n';return 1;}
}
