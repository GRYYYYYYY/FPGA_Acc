#include "native_csr_io.hpp"
#include "native_quotient.hpp"
#include "native_route_state.hpp"
#include "native_boundary_shadow.hpp"
#include "native_corridor.hpp"
#include "native_die_access.hpp"
#include <iostream>
#include <numeric>
using namespace dieroute;
using namespace dieroute::native;
struct Task {uint32_t id,net,source,sink,observer,sink_die;};
int main(int argc,char** argv){try{
    check(argc>=12&&argc<=21,"usage: route_native_cohort GRAPH SEARCH FOOTPRINT MAPPING QUOTIENT ARCH NEW_OUTPUT LABEL_LIMIT TASKS_PER_PAIR ITERATIONS REPEATS [SHADOW_SYNC_SEARCHES_0_OFF [CORRIDOR_ATTEMPTS_0_OFF [COMPARE_REENTRY_0_1 [BOUND_REENTRY_0_1 [PORTAL_CANDIDATES [JOINT_PORTALS_0_1 [DEFER_BUDGET_0_1 [OWNER_PARTITION_0_1 [DIE_WORKERS_0_1]]]]]]]]]");
    fs::path graph=argv[1],search=argv[2],fp=argv[3],mapping=argv[4],q=argv[5],out=argv[7];auto arch=fingerprint(argv[6]);
    auto limit=std::stoull(argv[8]),take=std::stoull(argv[9]),iterations=std::stoull(argv[10]),repeats=std::stoull(argv[11]);check(limit&&take&&iterations&&repeats,"positive cohort limits");
    const auto shadowSync=argc>=13?std::stoull(argv[12]):0;
    const auto corridorAttempts=argc>=14?std::stoull(argv[13]):0;check(corridorAttempts<UINT32_MAX,"corridor attempt range");
    const auto compareReentry=argc>=15?std::stoull(argv[14]):0;check(compareReentry<=1&&(!compareReentry||corridorAttempts),"corridor reentry mode");
    const auto portalCandidates=argc>=17?std::stoull(argv[16]):1;check(portalCandidates&&portalCandidates<UINT32_MAX&&(portalCandidates==1||corridorAttempts),"corridor candidate count");
    const auto boundReentry=argc>=16?std::stoull(argv[15]):0;check(boundReentry<=1&&(!boundReentry||compareReentry||portalCandidates>1),"corridor cost bound mode");
    const auto jointPortals=argc>=18?std::stoull(argv[17]):0;check(jointPortals<=1&&(!jointPortals||(corridorAttempts&&portalCandidates==1)),"joint portal search mode");
    const auto deferBudget=argc>=19?std::stoull(argv[18]):0;check(deferBudget<=1&&(!deferBudget||jointPortals),"joint budget scheduling mode");
    const auto ownerPartition=argc>=20?std::stoull(argv[19]):0;check(ownerPartition<=1,"native owner partition mode");
    const auto dieWorkers=argc>=21?std::stoull(argv[20]):0;check(dieWorkers<=1&&(!dieWorkers||(ownerPartition&&jointPortals&&!shadowSync)),"die workers require partitioned joint mode without source-observer shadows");
    check(fs::create_directory(out),"new cohort output required");
    Raw nodes(graph/"nodes.bin",16),tasks(fp/"tasks.bin",8),owners(fp/"owners.bin",2),nets(fp/"nets.bin",16),nm(mapping/"footprint_node_map.bin",1);
    std::unique_ptr<Raw> pips;if(corridorAttempts)pips=std::make_unique<Raw>(graph/"pips.bin",8);
    Container offsets(search/"offsets.bin",offsets_type,8,arch),arcs(search/"arcs.bin",arcs_type,8,arch),mask(search/"node_protection.bin",0x4452000a,1,arch),exclusive(search/"exclusive_net.bin",0x4452000b,4,arch);
    check(nodes.count<none&&offsets.count==nodes.count+1&&mask.count==nodes.count&&exclusive.count==nodes.count,"cohort table coverage");
    check(offsets.offset(0)==0&&offsets.offset(nodes.count)==arcs.count,"cohort CSR coverage");
    auto mapped=[&](uint32_t old){check(old<nm.count,"footprint node bounds");auto n=nm.at(old,0);check(n<nodes.count,"mapped node bounds");return n;};
    std::map<std::pair<uint32_t,uint32_t>,size_t> pairs;std::set<uint32_t> selected;std::vector<uint32_t> selectedTasks;
    uint32_t dies=1;
    for(size_t i=0;i<tasks.count;++i){check(tasks.at(i,0)==i,"task ID");check(tasks.at(i,4)<8&&tasks.at(i,5)<8,"task SLR range");dies=std::max(dies,1+std::max(tasks.at(i,4),tasks.at(i,5)));if(pairs[{tasks.at(i,4),tasks.at(i,5)}]++<take){selected.insert(tasks.at(i,1));selectedTasks.push_back(i);}}
    if(shadowSync||corridorAttempts||ownerPartition){
        // Workloads need not have endpoints on every available die. Derive the
        // broadcast domain from the full graph, not from selected task pairs.
        uint32_t topologyMask=0;for(size_t n=0;n<nodes.count;++n)topologyMask|=nodes.at(n,5);
        check(topologyMask&&topologyMask<256,"native graph SLR domain");
        while(topologyMask>>dies)++dies;
    }
    std::map<uint32_t,std::vector<Task>> cohort;
    for(size_t i=0;i<tasks.count;++i){auto net=tasks.at(i,1);if(selected.count(net)){check(net<nets.count&&nets.at(net,0)==0,"noncandidate cohort net");
        auto src=mapped(tasks.at(i,2)),dst=mapped(tasks.at(i,3));auto& group=cohort[net];check(group.empty()||group.front().source==src,"multiple native sources");group.push_back({uint32_t(i),net,src,dst,tasks.at(i,4),tasks.at(i,5)});}}
    std::vector<uint32_t> order(selected.begin(),selected.end());std::sort(order.begin(),order.end(),[&](auto a,auto b){return cohort.at(a).front().id<cohort.at(b).front().id;});
    std::vector<uint64_t> frozen((nodes.count+63)/64);size_t frozenCount=0;
    for(size_t i=0;i<owners.count;++i){auto net=owners.at(i,1);check(net<nets.count,"owner net bounds");if(selected.count(net))continue;auto n=mapped(owners.at(i,0));auto bit=uint64_t(1)<<(n%64);
        if(!(frozen[n/64]&bit)){frozen[n/64]|=bit;++frozenCount;}}
    auto allowed=[&](uint32_t n,uint32_t net){return n<nodes.count&&!mask.data[n]&&!(frozen[n/64]&(uint64_t(1)<<(n%64)))&&(le32(exclusive.data+4*n)==none||le32(exclusive.data+4*n)==net);};
    auto membership=[&](uint32_t n){check(n<nodes.count,"owner node bounds");return nodes.at(n,5);};
    const auto layout=ownerPartition?NativeOwnerLayout::from_membership(dies,membership):NativeOwnerLayout{};
    auto pipDie=[&](uint32_t key){auto id=key>>1;check(pips&&id<pips->count&&pips->at(id,0)==id,"corridor PIP identity");auto die=pips->at(id,6);check(die<dies,"corridor PIP SLR range");return die;};
    std::vector<NativePortal> portals;
    if(corridorAttempts)for(size_t n=0;n<nodes.count;++n){auto m=membership(n);
        if(!(m&(m-1))||mask.data[n]||(frozen[n/64]&(uint64_t(1)<<(n%64))))continue;
        uint32_t exits=0;for(auto e=offsets.offset(n);e<offsets.offset(n+1);++e)exits|=1U<<pipDie(arcs.edge(e));
        portals.push_back({uint32_t(n),m,exits});}
    auto geometry=[&](uint32_t a,uint32_t b){uint64_t gap=0;
        for(unsigned axis=0;axis<2;++axis){auto al=nodes.at(a,9+axis),ah=nodes.at(a,11+axis),bl=nodes.at(b,9+axis),bh=nodes.at(b,11+axis);
            check(al<=ah&&bl<=bh,"corridor proposal coordinate bounds");if(ah<bl)gap+=uint64_t(bl)-ah;else if(bh<al)gap+=uint64_t(al)-bh;}return gap;};
    auto edgeValid=[&](uint32_t src,uint32_t dst,uint32_t key){auto lo=offsets.offset(src),end=offsets.offset(src+1),hi=end;check(lo<=end&&end<=arcs.count,"CSR row bounds");
        while(lo<hi){auto mid=lo+(hi-lo)/2;if(std::make_pair(arcs.dst(mid),arcs.edge(mid))<std::make_pair(dst,key))lo=mid+1;else hi=mid;}
        return lo<end&&arcs.dst(lo)==dst&&arcs.edge(lo)==key;};
    for(const auto& [net,group]:cohort)for(const auto& t:group)check(allowed(t.source,net)&&allowed(t.sink,net),"cohort endpoint frozen or forbidden");
    std::ofstream selection(out/"selection.csv");selection<<"task,net,source,sink,selection_seed\n";size_t taskCount=0;
    for(auto net:order)for(const auto& t:cohort.at(net)){selection<<t.id<<','<<net<<','<<t.source<<','<<t.sink<<','<<std::binary_search(selectedTasks.begin(),selectedTasks.end(),t.id)<<'\n';++taskCount;}
    selection.close();check(bool(selection),"selection output failure");
    std::ofstream logs(out/"iterations.csv"),connections(out/"connections.csv"),paths(out/"paths.csv"),treeOut(out/"trees.csv"),usage(out/"usage.csv");
    logs<<"repeat,iteration,present,pending_nets,routed_tasks,failed_tasks,overused_nodes,expanded,edge_visits,quotient_expanded,quotient_edge_visits,max_labels,deferred_retries\n";
    connections<<"repeat,task,net,status,full_hops\n";paths<<"repeat,task,step,source,destination,pip_key\n";
    treeOut<<"repeat,net,node,parent,pip_key,depth\n";usage<<"repeat,node,net,history,version\n";
    std::ofstream shadowTrace(out/"shadow_trace.csv"),shadowMetrics(out/"shadow_metrics.csv"),shadowReads(out/"shadow_reads.csv"),shadowFinal(out/"shadow_final.csv");
    shadowTrace<<"repeat,search,iteration,task,observer,remote_reads,read_hash,stale,overflow,initial_status,final_status,initial_expanded,replay_expanded\n";
    shadowReads<<"repeat,search,node,observed_occupancy,observed_history,observed_version,current_occupancy,current_history,current_version\n";
    shadowFinal<<"repeat,node,occupancy,history,version\n";
    shadowMetrics<<"repeat,sync_searches,searches,replays,remote_reads,publications,changed_summaries,logical_deliveries,retained_summaries\n";
    std::ofstream corridorRuns(out/"corridor_runs.csv"),corridorTrace(out/"corridor_trace.csv"),corridorPaths(out/"corridor_paths.csv"),corridorCandidates(out/"corridor_candidates.csv");
    corridorRuns<<"repeat,search,replay,iteration,task,plans,local_searches,flat_searches,repairs,fallbacks,reserved,released,retained,overcapacity,ranked,cost_prunes,joint_searches,budget_deferrals,joint_expanded,joint_edge_visits,local_expanded,local_edge_visits,flat_expanded,flat_edge_visits,pass,fallback_mode,status,attachment,hops,cost,expanded,edge_visits\n";
    corridorTrace<<"repeat,search,replay,attempt,stage,die,portal,completed,selected,failed_stage,attachment,hops,cost,search_status,expanded,edge_visits\n";
    std::ofstream passes(out/"cohort_passes.csv");passes<<"repeat,iteration,net,pass,rescue,tree_before,tree_after,failed_tasks,budget_deferred,will_retry\n";
    corridorPaths<<"repeat,search,replay,step,source,destination,pip_key\n";
    corridorCandidates<<"repeat,search,replay,attempt,step,source,destination,pip_key\n";
    std::ofstream ownerUsage(out/"owner_usage.csv");ownerUsage<<"repeat,owner,node,net,history,version\n";
    std::ofstream workerQueues(out/"worker_queues.csv"),workerReads(out/"worker_reads.csv"),workerAccess(out/"worker_access.csv");
    workerQueues<<"repeat,search,replay,attempt,die,expanded,edge_visits,pushes,transfers,labels\n";
    workerReads<<"repeat,search,replay,worker,owner,node,occupancy,history,version\n";
    workerAccess<<"repeat,search,replay,worker,owned_reads,requests,cache_hits,validations,valid\n";
    std::ofstream transport(out/"worker_transport.csv");transport<<"repeat,search,replay,attempt,die,probes,probe_protected,relaxes,accepted,rejected,traces,epoch_rejects\n";
    Writer packets(out/"worker_packets.bin",0x44520020,0,arch);
    size_t successfulRepeats=0;QuotientPotential potential(q,arch,nodes.count);SparseSearch workspace;
    for(size_t rep=0;rep<repeats;++rep){NativeRouteState state(layout);std::map<uint32_t,SparseSearchStatus> statuses;
        for(auto net:order){state.start(net,cohort.at(net).front().source,allowed);for(const auto& t:cohort.at(net))statuses[t.id]=SparseSearchStatus::exhausted;}
        NativeBoundaryShadows shadows(dies);uint64_t searches=0,replays=0,remoteReads=0;
        NativeCorridorRouter corridor(portals,dies,uint32_t(corridorAttempts),bool(compareReentry),bool(boundReentry),uint32_t(portalCandidates),bool(jointPortals),bool(dieWorkers));
        std::set<uint32_t> pending=selected;uint64_t present=1;
        for(size_t epoch=0;epoch<iterations;++epoch){if(epoch)for(auto net:pending){state.ripup(net);for(const auto& t:cohort.at(net))statuses.at(t.id)=SparseSearchStatus::exhausted;}
            uint64_t expanded=0,visits=0,qexpanded=0,qvisits=0;size_t maxLabels=0,deferred=0;
            for(auto net:order)if(pending.count(net)){
              bool retry=true,rescue=false;size_t pass=0;
              while(retry){auto before=state.tree(net).nodes.size();size_t failed=0,budgetDeferred=0;
               const auto fallbackMode=deferBudget?(rescue?NativeFallbackMode::flat_rescue:NativeFallbackMode::defer_budget):NativeFallbackMode::immediate;
               for(const auto& t:cohort.at(net)){
                if(pass&&statuses.at(t.id)==SparseSearchStatus::found)continue;
                if(pass)++deferred;
                SparseSearchResult branch;bool branchDeferred=false;
                if(state.tree(net).nodes.count(t.sink)){branch.status=SparseSearchStatus::found;branch.attachment=t.sink;branch.hops=state.tree(net).nodes.at(t.sink).depth;}
                else {if(!corridorAttempts){potential.prepare(t.sink,t.source);qexpanded+=potential.expanded;qvisits+=potential.edge_visits;}
                    if(shadowSync && searches%shadowSync==0)shadows.publish(state,membership);
                    std::optional<NativeBoundaryShadows::View> view;
                    if(shadowSync)view.emplace(shadows,t.observer,net,present);
                    uint64_t initialExpanded=0,replayExpanded=0;
                    unsigned invocation=0;
                    auto run=[&](bool useShadow,uint64_t& attemptExpanded){
                        if(corridorAttempts){
                            auto before=corridor.metrics();auto oldVisits=visits,oldExpanded=attemptExpanded;
                            const auto currentInvocation=invocation++;SparseSearchResult result;std::exception_ptr overflowError;
                            std::optional<NativeDieAccess> workerView;if(dieWorkers)workerView.emplace(state,net,present);
                            try{result=corridor.run(state,net,t.sink,t.sink_die,nodes.count,workspace,{size_t(limit),UINT64_MAX},
                                [&](uint32_t n,auto emit){for(auto e=offsets.offset(n);e<offsets.offset(n+1);++e){auto dst=arcs.dst(e);if(allowed(dst,net))emit(dst,arcs.edge(e),pipDie(arcs.edge(e)));}},
                                membership,[&](uint32_t n){return allowed(n,net);},[&](uint32_t n,uint32_t die){return dieWorkers&&die!=none?workerView->cost(die,n,membership(n)):useShadow?view->cost(state,n,membership(n)):state.cost(n,net,present);},
                                [&](uint32_t goal,uint64_t ceiling){potential.prepare(goal,t.source,ceiling);qexpanded+=potential.expanded;qvisits+=potential.edge_visits;},[&](uint32_t n){return potential(n);},geometry,attemptExpanded,visits,maxLabels,fallbackMode);}
                            catch(const std::overflow_error&){overflowError=std::current_exception();}
                            if(workerView){const auto valid=workerView->validate();
                                for(uint32_t die=0;die<dies;++die){const auto& m=workerView->metrics(die);workerAccess<<rep<<','<<searches<<','<<currentInvocation<<','<<die<<','<<m.owned_reads<<','<<m.requests<<','<<m.cache_hits<<','<<m.validations<<','<<valid<<'\n';}
                                workerView->observations([&](uint32_t worker,uint32_t owner,uint32_t node,const auto& v){workerReads<<rep<<','<<searches<<','<<currentInvocation<<','<<worker<<','<<owner<<','<<node<<','<<v.occupancy<<','<<v.history<<','<<v.version<<'\n';});
                                check(valid,"serialized worker read phase invalidated before commit");}
                            result.expanded=attemptExpanded-oldExpanded;result.edge_visits=visits-oldVisits;
                            const auto& m=corridor.metrics();corridorRuns<<rep<<','<<searches<<','<<currentInvocation<<','<<epoch<<','<<t.id;
#define DELTA(field) corridorRuns<<','<<(m.field-before.field)
                            DELTA(plans);DELTA(local_searches);DELTA(flat_searches);DELTA(repairs);DELTA(fallbacks);DELTA(reserved);DELTA(released);DELTA(retained);DELTA(overcapacity);DELTA(ranked);DELTA(cost_prunes);DELTA(joint_searches);DELTA(budget_deferrals);DELTA(joint_expanded);DELTA(joint_edge_visits);DELTA(local_expanded);DELTA(local_edge_visits);DELTA(flat_expanded);DELTA(flat_edge_visits);
#undef DELTA
                            branchDeferred=m.budget_deferrals>before.budget_deferrals;
                            corridorRuns<<','<<pass<<','<<static_cast<int>(fallbackMode)<<','<<(overflowError?-1:static_cast<int>(result.status))<<','<<result.attachment<<','<<result.hops<<','<<result.cost<<','<<result.expanded<<','<<result.edge_visits<<'\n';
                            for(size_t attempt=0;attempt<corridor.trace().size();++attempt){const auto& r=corridor.trace()[attempt];for(size_t stage=0;stage<r.dies.size();++stage){
                                corridorTrace<<rep<<','<<searches<<','<<currentInvocation<<','<<attempt<<','<<stage<<','<<r.dies[stage]<<','<<(stage<r.portals.size()?r.portals[stage]:none)<<','<<r.completed<<','<<r.selected<<','<<r.failed_stage<<','<<r.attachment<<','<<r.hops<<','<<r.cost<<','<<r.search_status<<','<<r.expanded<<','<<r.edge_visits<<'\n';}
                                auto parent=r.attachment;for(size_t step=0;step<r.path.size();++step){corridorCandidates<<rep<<','<<searches<<','<<currentInvocation<<','<<attempt<<','<<step<<','<<parent<<','<<r.path[step]<<','<<r.edges[step]<<'\n';parent=r.path[step];}}
                            if(dieWorkers)for(size_t attempt=0;attempt<corridor.trace().size();++attempt){const auto& r=corridor.trace()[attempt];
                                for(size_t die=0;die<r.workers.size();++die){const auto& m=r.workers[die];workerQueues<<rep<<','<<searches<<','<<currentInvocation<<','<<attempt<<','<<die<<','<<m.expanded<<','<<m.edge_visits<<','<<m.pushes<<','<<m.transfers<<','<<m.labels<<'\n';
                                    transport<<rep<<','<<searches<<','<<currentInvocation<<','<<attempt<<','<<die<<','<<m.probes<<','<<m.probe_protected<<','<<m.relaxes<<','<<m.accepted<<','<<m.rejected<<','<<m.traces<<','<<m.epoch_rejects<<'\n';}
                                for(size_t sequence=0;sequence<r.packets.size();++sequence){std::array<unsigned char,128> frame{};put64(frame.data(),rep);put64(frame.data()+8,searches);put64(frame.data()+16,currentInvocation);put64(frame.data()+24,attempt);put64(frame.data()+32,sequence);
                                    const auto wire=r.packets[sequence].encode();std::copy(wire.begin(),wire.end(),frame.begin()+64);packets.append(frame.data(),frame.size());}}
                            auto from=result.attachment;for(size_t step=0;step<result.path.size();++step){corridorPaths<<rep<<','<<searches<<','<<currentInvocation<<','<<step<<','<<from<<','<<result.path[step]<<','<<result.edges[step]<<'\n';from=result.path[step];}
                            if(overflowError)std::rethrow_exception(overflowError);
                            return result;
                        }
                        return workspace.run_guided(nodes.count,state.seeds(net),t.sink,UINT32_MAX,[&](uint32_t n,auto offer){
                        auto begin=offsets.offset(n),end=offsets.offset(n+1);check(begin<=end&&end<=arcs.count,"CSR row bounds");
                        for(auto edge=begin;edge<end;++edge){auto dst=arcs.dst(edge);check(dst<nodes.count,"CSR destination bounds");if(allowed(dst,net))offer(dst,arcs.edge(edge),[&](){return std::optional<uint64_t>(useShadow?view->cost(state,dst,membership(dst)):state.cost(dst,net,present));});}
                    },[&](uint32_t n){return potential(n);},{size_t(limit),UINT64_MAX},&attemptExpanded,&visits);};
                    bool overflow=false;
                    try{branch=run(bool(view),initialExpanded);}catch(const std::overflow_error&){overflow=true;}
                    maxLabels=std::max(maxLabels,workspace.touched());
                    const auto initialStatus=overflow?-1:static_cast<int>(branch.status);
                    const bool stale=view&&!view->valid(state);
                    if(overflow&&!stale)throw std::overflow_error("current native search cost overflow");
                    if(stale){++replays;branch=run(false,replayExpanded);maxLabels=std::max(maxLabels,workspace.touched());}
                    if(view){remoteReads+=view->reads();shadowTrace<<rep<<','<<searches<<','<<epoch<<','<<t.id<<','<<t.observer<<','<<view->reads()<<','<<view->read_hash()<<','<<stale<<','<<overflow<<','<<initialStatus<<','<<static_cast<int>(branch.status)<<','<<initialExpanded<<','<<replayExpanded<<'\n';
                        view->observations(state,[&](uint32_t n,const auto& seen,const auto& now){shadowReads<<rep<<','<<searches<<','<<n<<','<<seen.occupancy<<','<<seen.history<<','<<seen.version<<','<<now.occupancy<<','<<now.history<<','<<now.version<<'\n';});}
                    ++searches;expanded+=initialExpanded+replayExpanded;
                }
                statuses.at(t.id)=branch.status;if(branch.status==SparseSearchStatus::found)state.accept(net,t.sink,branch,allowed,edgeValid);else {++failed;budgetDeferred+=branchDeferred;}
                std::cout<<"repeat="<<rep<<" epoch="<<epoch<<" pass="<<pass<<" task="<<t.id<<" net="<<net<<" found="<<(branch.status==SparseSearchStatus::found)<<" tree_nodes="<<state.tree(net).nodes.size()<<" expanded="<<branch.expanded<<std::endl;
               }
               const auto after=state.tree(net).nodes.size();retry=failed&&after>before;
               const bool enterRescue=deferBudget&&!rescue&&budgetDeferred&&after==before;
               if(enterRescue)retry=true;
               passes<<rep<<','<<epoch<<','<<net<<','<<pass<<','<<rescue<<','<<before<<','<<after<<','<<failed<<','<<budgetDeferred<<','<<retry<<'\n';
               if(enterRescue)rescue=true;
               ++pass;
              }
            }
            size_t routed=0;std::set<uint32_t> next;
            for(auto net:order)for(const auto& t:cohort.at(net)){if(statuses.at(t.id)==SparseSearchStatus::found)++routed;else next.insert(net);}
            auto overused=state.overused();logs<<rep<<','<<epoch<<','<<present<<','<<pending.size()<<','<<routed<<','<<(taskCount-routed)<<','<<overused<<','<<expanded<<','<<visits<<','<<qexpanded<<','<<qvisits<<','<<maxLabels<<','<<deferred<<'\n';logs.flush();
            if(routed==taskCount&&!overused){++successfulRepeats;break;}
            if(epoch+1==iterations)break;
            auto congested=state.negotiate(1);next.insert(congested.begin(),congested.end());pending=std::move(next);
            if(present>UINT64_MAX/2)throw std::overflow_error("native present factor overflow");
            present*=2;
        }
        for(auto net:order){for(const auto& [n,value]:state.tree(net).nodes)treeOut<<rep<<','<<net<<','<<n<<','<<value.parent<<','<<value.pip<<','<<value.depth<<'\n';
            for(const auto& t:cohort.at(net)){const auto status=statuses.at(t.id);const char* name=status==SparseSearchStatus::found?"found":status==SparseSearchStatus::budget_exhausted?"budget_exhausted":status==SparseSearchStatus::hop_limited?"hop_limited":"exhausted";
                auto path=status==SparseSearchStatus::found?state.path(net,t.sink):std::vector<std::pair<uint32_t,uint32_t>>{};connections<<rep<<','<<t.id<<','<<net<<','<<name<<','<<path.size()<<'\n';auto from=t.source;
                for(size_t i=0;i<path.size();++i){paths<<rep<<','<<t.id<<','<<i<<','<<from<<','<<path[i].first<<','<<path[i].second<<'\n';from=path[i].first;}}
        }
        state.visit_uses([&](auto node,const auto& u){
            if(u.nets.empty())usage<<rep<<','<<node<<','<<none<<','<<u.history<<','<<u.version<<'\n';
            else for(auto net:u.nets)usage<<rep<<','<<node<<','<<net<<','<<u.history<<','<<u.version<<'\n';});
        for(uint32_t die=0;die<state.owner_count();++die)for(const auto& [node,u]:state.owner_uses(die)){
            if(u.nets.empty())ownerUsage<<rep<<','<<die<<','<<node<<','<<none<<','<<u.history<<','<<u.version<<'\n';
            else for(auto net:u.nets)ownerUsage<<rep<<','<<die<<','<<node<<','<<net<<','<<u.history<<','<<u.version<<'\n';}
        // Drain all pending summaries before comparing communication counts.
        // A delayed publisher must not claim savings by omitting its tail.
        if(shadowSync){shadows.publish(state,membership);shadows.summaries([&](uint32_t n,const auto& s){shadowFinal<<rep<<','<<n<<','<<s.occupancy<<','<<s.history<<','<<s.version<<'\n';});}
        const auto& m=shadows.metrics();shadowMetrics<<rep<<','<<shadowSync<<','<<searches<<','<<replays<<','<<remoteReads<<','<<m.publications<<','<<m.changed_summaries<<','<<m.logical_deliveries<<','<<shadows.records()<<'\n';
    }
    logs.close();connections.close();paths.close();treeOut.close();usage.close();check(bool(logs)&&bool(connections)&&bool(paths)&&bool(treeOut)&&bool(usage),"cohort output failure");
    shadowTrace.close();shadowMetrics.close();shadowReads.close();shadowFinal.close();check(bool(shadowTrace)&&bool(shadowMetrics)&&bool(shadowReads)&&bool(shadowFinal),"shadow output failure");
    corridorRuns.close();corridorTrace.close();corridorPaths.close();corridorCandidates.close();check(bool(corridorRuns)&&bool(corridorTrace)&&bool(corridorPaths)&&bool(corridorCandidates),"corridor output failure");
    packets.finish_dynamic(128);transport.close();check(bool(transport),"transport output failure");
    workerQueues.close();workerReads.close();workerAccess.close();check(bool(workerQueues)&&bool(workerReads)&&bool(workerAccess),"worker output failure");
    ownerUsage.close();check(bool(ownerUsage),"owner inventory output failure");
    passes.close();check(bool(passes),"cohort pass output failure");
    std::ofstream report(out/"audit.json");report<<"{\"schema\":\"dieroute.native_cohort_route.v1\",\"selected_seed_tasks\":"<<selectedTasks.size()<<",\"selected_nets\":"<<selected.size()<<",\"all_selected_net_tasks\":"<<taskCount<<",\"frozen_unselected_footprint_nodes\":"<<frozenCount<<",\"repeats\":"<<repeats<<",\"electrical_model_converged_repeats\":"<<successfulRepeats<<",\"native_design_legal\":null,\"scope\":\"whole selected nets, fixed other original footprints, shared trees and negotiated electrical-node exclusivity; hop/congestion objective, not physical timing or full-design native legality/QoR\"}\n";
    report.close();check(bool(report),"cohort audit output failure");return 0;
}catch(const std::exception& e){std::cerr<<"native cohort route failed: "<<e.what()<<std::endl;return 1;}}
