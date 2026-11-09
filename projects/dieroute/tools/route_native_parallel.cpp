#include "native_csr_io.hpp"
#include "native_quotient.hpp"
#include "native_route_state.hpp"
#include "native_boundary_shadow.hpp"
#include "native_corridor.hpp"
#include "native_net_transaction.hpp"
#include "native_summary_hbm.hpp"
#include "native_net_commit.hpp"
#include <iostream>
#include <numeric>
using namespace dieroute;
using namespace dieroute::native;
struct Task {uint32_t id,net,source,sink,observer,sink_die;};
int main(int argc,char** argv){try{
    check(argc==22||argc==23||argc==24||argc==25,"usage: route_native_cohort GRAPH SEARCH FOOTPRINT MAPPING QUOTIENT ARCH NEW_OUTPUT LABEL_LIMIT TASKS_PER_PAIR ITERATIONS REPEATS [SHADOW_SYNC_SEARCHES_0_OFF [CORRIDOR_ATTEMPTS_0_OFF [COMPARE_REENTRY_0_1 [BOUND_REENTRY_0_1 [PORTAL_CANDIDATES [JOINT_PORTALS_0_1 [DEFER_BUDGET_0_1 [OWNER_PARTITION_0_1 [DIE_WORKERS_0_1]]]]]]]]] NET_WORKERS");
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
    const auto netWorkers=std::stoull(argv[21]);check(netWorkers>=1&&netWorkers<=8&&dieWorkers&&deferBudget&&!shadowSync,"parallel nets require 1..8 workers and partitioned joint/deferred mode without source shadows");
    const auto workerShadowSync=argc>=23?std::stoull(argv[22]):0;
    const auto summaryHbm=argc>=24?std::stoull(argv[23]):0;check(summaryHbm<=2&&(!summaryHbm||workerShadowSync),"HBM endpoint requires persistent summaries");
    const auto netCommit=argc==25?std::stoull(argv[24]):0;check(netCommit<=1&&(!netCommit||summaryHbm==2),"net authority requires owner publisher mode");
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
    std::ofstream logs(out/"iterations.csv"),connections(out/"connections.csv"),paths(out/"paths.csv"),treeOut(out/"trees.csv"),usage(out/"usage.csv"),ownerUsage(out/"owner_usage.csv");
    logs<<"repeat,iteration,present,pending_nets,routed_tasks,failed_tasks,overused_nodes,expanded,edge_visits,quotient_expanded,quotient_edge_visits,max_labels,deferred_retries\n";
    connections<<"repeat,task,net,status,full_hops\n";paths<<"repeat,task,step,source,destination,pip_key\n";
    treeOut<<"repeat,net,node,parent,pip_key,depth\n";usage<<"repeat,node,net,history,version\n";ownerUsage<<"repeat,owner,node,net,history,version\n";
    std::ofstream tx(out/"transactions.csv"),branches(out/"proposals.csv"),branchPaths(out/"proposal_paths.csv"),passes(out/"transaction_passes.csv"),conflicts(out/"conflicts.csv"),execution(out/"execution.csv"),acceptedWork(out/"accepted_work.csv");
    tx<<"repeat,iteration,wave,slot,net,attempt,read_begin,reads,conflicts,tree_changed,overflow,committed,expanded,edge_visits,quotient_expanded,quotient_edge_visits,max_labels,deferred_retries,label_packets,branches,passes\n";
    branches<<"repeat,iteration,wave,slot,attempt,branch,task,net,sink,sink_die,pass,rescue,deferred,status,attachment,hops,cost,expanded,edge_visits\n";
    branchPaths<<"repeat,iteration,wave,slot,attempt,branch,step,source,destination,pip_key\n";
    passes<<"repeat,iteration,wave,slot,attempt,pass,tree_before,tree_after,failed_tasks,budget_deferred,rescue,will_retry\n";
    conflicts<<"repeat,iteration,wave,slot,attempt,node,snapshot_version,current_version\n";
    execution<<"repeat,iteration,wave,slot,net,begin_ns,end_ns\n";
    acceptedWork<<"repeat,iteration,expanded,edge_visits,quotient_expanded,quotient_edge_visits,max_labels,deferred_retries\n";
    Writer readsets(out/"readsets.bin",0x44520021,0,arch);uint64_t readCount=0;
    Writer shadowPackets(out/"worker_shadow_messages.bin",0x44520022,0,arch);
    std::ofstream shadowReads(out/"persistent_shadow_reads.csv"),shadowChecks(out/"persistent_shadow_checks.csv"),shadowBranches(out/"persistent_shadow_branches.csv"),shadowPublications(out/"persistent_shadow_publications.csv");
    shadowReads<<"repeat,iteration,wave,slot,attempt,query,branch,worker,node,occupancy,history,version,hit\n";
    shadowChecks<<"repeat,iteration,wave,slot,attempt,queries,stale\n";
    shadowBranches<<"repeat,iteration,wave,slot,attempt,branch,shadow_path\n";
    shadowPublications<<"repeat,iteration,wave,slot,attempt,reason,window,scans,messages,retained\n";
    auto messages=[&](const auto& packets,size_t rep,size_t epoch,size_t wave,size_t slot,unsigned attempt,unsigned reason){
        for(size_t i=0;i<packets.size();++i){std::array<unsigned char,128> frame{};put64(frame.data(),rep);put64(frame.data()+8,epoch);put64(frame.data()+16,wave);put64(frame.data()+24,slot);put64(frame.data()+32,attempt);put64(frame.data()+40,reason);put64(frame.data()+48,i);
            auto wire=packets[i].encode();std::copy(wire.begin(),wire.end(),frame.begin()+64);shadowPackets.append(frame.data(),frame.size());}
    };

    std::unique_ptr<NativeNetCommit> authority;
    if(netCommit){std::vector<uint64_t> policy(nodes.count);
        for(size_t n=0;n<nodes.count;++n)policy[n]=le32(exclusive.data+4*n)|(uint64_t(membership(n))<<32)|((uint64_t(bool(mask.data[n])||bool(frozen[n/64]&(uint64_t(1)<<(n%64))))<<40));
        authority=std::make_unique<NativeNetCommit>(layout,std::move(policy),reinterpret_cast<const uint64_t*>(offsets.data),reinterpret_cast<const uint64_t*>(arcs.data),arcs.count,order,out,arch);
    }
    std::unique_ptr<NativeSummaryHbm> fabric;
    if(summaryHbm){std::vector<uint32_t> boundary;for(size_t n=0;n<nodes.count;++n){auto m=membership(n);if(m&(m-1))boundary.push_back(n);}fabric=std::make_unique<NativeSummaryHbm>(layout,std::move(boundary),netWorkers,summaryHbm==2);}
    Writer endpointFrames(out/"summary_hbm_frames.bin",0x44520024,0,arch),endpointTopology(out/"summary_hbm_topology.bin",0x44520023,0,arch);
    if(fabric)for(auto value:fabric->topology()){unsigned char b[8];put64(b,value);endpointTopology.append(b,8);}
    endpointTopology.finish_dynamic(8);
    std::ofstream endpointOwners(out/"summary_hbm_owners.csv"),endpointCaches(out/"summary_hbm_caches.csv");
    std::ofstream endpointSubscriptions;if(summaryHbm==2){endpointSubscriptions.open(out/"summary_hbm_subscriptions.csv");endpointSubscriptions<<"repeat,owner,node,subscribers,pending,queued\n";}
    endpointOwners<<"repeat,owner,node,occupancy,history,version\n";endpointCaches<<"repeat,lane,worker,node,occupancy,history,version\n";
    uint64_t endpointSequence=0;
    auto endpointTrace=[&](size_t rep,size_t epoch,size_t wave,size_t actor,unsigned attempt,unsigned reason){if(!fabric)return;
        auto frames=fabric->take_frames(actor);for(size_t i=0;i<frames.size();++i){std::array<unsigned char,384> b{};const uint64_t prefix[]={rep,epoch,wave,actor,attempt,frames[i].reason==UINT32_MAX?reason:frames[i].reason,endpointSequence++,frames[i].die};
            for(unsigned j=0;j<8;++j)put64(b.data()+j*8,prefix[j]);
            for(unsigned w=0;w<5;++w)for(unsigned j=0;j<8;++j)put64(b.data()+64+w*64+j*8,frames[i].words[w].w[j]);
            endpointFrames.append(b.data(),b.size());}
    };
    struct Lane {QuotientPotential potential;SparseSearch search;NativeCorridorRouter corridor;std::unique_ptr<NativeWorkerShadows> shadows=std::make_unique<NativeWorkerShadows>();
        Lane(const fs::path& q,const Fingerprint& arch,size_t nodes,const std::vector<NativePortal>& portals,uint32_t dies,uint32_t attempts,bool reentry,bool bound,uint32_t candidates)
          :potential(q,arch,nodes),corridor(portals,dies,attempts,reentry,bound,candidates,true,true){}
    };
    std::vector<std::unique_ptr<Lane>> lanes;
    for(size_t i=0;i<netWorkers;++i)lanes.push_back(std::make_unique<Lane>(q,arch,nodes.count,portals,dies,corridorAttempts,compareReentry,boundReentry,portalCandidates));
    if(fabric)for(size_t i=0;i<lanes.size();++i)lanes[i]->shadows=std::make_unique<NativeHbmShadows>(*fabric,i);
    size_t successfulRepeats=0;
    for(size_t rep=0;rep<repeats;++rep){endpointSequence=0;NativeRouteState state(layout),oracle(layout);
        if(authority){authority->context(rep,UINT32_MAX,0,UINT32_MAX,0);authority->initialize(rep+1);state=authority->snapshot();NativeNetCommit::compare(state,oracle);}std::map<uint32_t,SparseSearchStatus> statuses;
        for(auto net:order){if(authority){authority->context(rep,UINT32_MAX,0,net,0);authority->start(net,cohort.at(net).front().source);state=authority->snapshot();oracle.start(net,cohort.at(net).front().source,allowed);NativeNetCommit::compare(state,oracle);}else state.start(net,cohort.at(net).front().source,allowed);for(const auto& t:cohort.at(net))statuses[t.id]=SparseSearchStatus::exhausted;}
        std::set<uint32_t> pending=selected;uint64_t present=1;size_t shadowWindow=0;
        if(fabric)fabric->reset(rep+1);
        if(workerShadowSync)for(auto& lane:lanes)lane->shadows->reset(layout,rep+1);
        auto publish=[&](size_t epoch,size_t wave,unsigned attempt){if(!fabric)return;
            if(authority){authority->context(rep,epoch,wave,fabric->controller(),attempt);fabric->publish_deltas(authority->publications(fabric->topology()));}
            else fabric->publish(state);
        };
        auto refresh=[&](size_t slot,size_t epoch,size_t wave,unsigned attempt,unsigned reason){
            auto& cache=*lanes.at(slot)->shadows;auto before=cache.metrics.scans;auto packets=cache.refresh(state);
            shadowPublications<<rep<<','<<epoch<<','<<wave<<','<<slot<<','<<attempt<<','<<reason<<','<<shadowWindow<<','<<(cache.metrics.scans-before)<<','<<packets.size()<<','<<cache.size()<<'\n';
            messages(packets,rep,epoch,wave,slot,attempt,reason);
            endpointTrace(rep,epoch,wave,slot,attempt,2);
        };
        for(size_t epoch=0;epoch<iterations;++epoch){if(epoch)for(auto net:pending){if(authority){authority->context(rep,epoch,UINT32_MAX,net,0);authority->ripup(net);state=authority->snapshot();oracle.ripup(net);NativeNetCommit::compare(state,oracle);}else state.ripup(net);for(const auto& t:cohort.at(net))statuses.at(t.id)=SparseSearchStatus::exhausted;}
            uint64_t expanded=0,visits=0,qexpanded=0,qvisits=0,acceptedExpanded=0,acceptedVisits=0,acceptedQexpanded=0,acceptedQvisits=0;
            size_t maxLabels=0,deferred=0,acceptedLabels=0,acceptedDeferred=0;
            std::vector<uint32_t> jobs;for(auto net:order)if(pending.count(net))jobs.push_back(net);
            auto execute=[&](size_t slot,uint32_t net,std::shared_ptr<const NativeRouteState> snapshot){
                auto& lane=*lanes.at(slot);uint64_t qe=0,qv=0;std::vector<NativeNetTask> tasks;
                for(const auto& t:cohort.at(net))tasks.push_back({t.id,t.sink,t.sink_die});
                auto proposal=native_propose_net(std::move(snapshot),net,tasks,present,nodes.count,size_t(limit),lane.corridor,lane.search,
                    [&](uint32_t n,auto emit){for(auto e=offsets.offset(n);e<offsets.offset(n+1);++e){auto dst=arcs.dst(e);if(allowed(dst,net))emit(dst,arcs.edge(e),pipDie(arcs.edge(e)));}},
                    membership,allowed,edgeValid,[&](uint32_t goal,uint64_t ceiling){lane.potential.prepare(goal,cohort.at(net).front().source,ceiling);qe+=lane.potential.expanded;qv+=lane.potential.edge_visits;},
                    [&](uint32_t n){return lane.potential(n);},geometry,true,workerShadowSync?lane.shadows.get():nullptr);
                proposal.quotient_expanded=qe;proposal.quotient_edge_visits=qv;return proposal;
            };
            for(size_t begin=0,wave=0;begin<jobs.size();begin+=netWorkers,++wave){
                std::vector<uint32_t> batch(jobs.begin()+begin,jobs.begin()+std::min(jobs.size(),begin+size_t(netWorkers)));
                if(fabric){publish(epoch,wave,0);endpointTrace(rep,epoch,wave,fabric->controller(),0,1);}
                if(workerShadowSync&&shadowWindow%workerShadowSync==0)for(size_t slot=0;slot<lanes.size();++slot)refresh(slot,epoch,wave,0,1);
                std::map<uint32_t,uint64_t> generations;if(authority)for(auto net:batch)generations[net]=authority->generation(net);
                auto snapshot=std::make_shared<const NativeRouteState>(state);
                auto proposed=native_parallel_propose(batch,[&](size_t slot,uint32_t net){return execute(slot,net,snapshot);});
                for(size_t slot=0;slot<proposed.size();++slot)endpointTrace(rep,epoch,wave,slot,0,0);
                auto validate=[&](size_t slot,const NativeNetProposal& p,unsigned attempt){
                    auto v=native_validate_net(authority?oracle:state,p,present);
                    if(fabric){publish(epoch,wave,2*(slot+1)+attempt);endpointTrace(rep,epoch,wave,fabric->controller(),2*(slot+1)+attempt,1);auto stale=fabric->validate(slot,p.shadow_reads);
                        check(stale==v.stale_shadows,"HBM/CPU observed-summary validation disagreement");v.stale_shadows=std::move(stale);endpointTrace(rep,epoch,wave,slot,attempt,3);}
                    return v;
                };
                auto commit=[&](size_t slot,const NativeNetProposal& p,const NativeNetValidation& validation,unsigned attempt){
                    if(!authority)return validation.valid()&&native_commit_net(state,p,present,allowed,edgeValid);
                    auto generation=attempt?authority->generation(p.net):generations.at(p.net);
                    authority->context(rep,epoch,wave,slot,attempt);bool accepted=authority->commit(p,generation);const auto& done=authority->completion();
                    check(done.w[2]==p.reads.size()&&done.w[3]==validation.conflicts.size()&&done.w[4]==validation.stale_shadows.size()&&done.w[5]==validation.tree_changed&&accepted==validation.valid(),"net kernel validation differs from independent oracle");
                    bool reference=native_commit_net(oracle,p,present,allowed,edgeValid);check(reference==accepted,"net kernel commit differs from independent oracle");
                    state=authority->snapshot();NativeNetCommit::compare(state,oracle);return accepted;
                };
                for(size_t slot=0;slot<proposed.size();++slot){
                    auto& initial=proposed[slot];execution<<rep<<','<<epoch<<','<<wave<<','<<slot<<','<<initial.net<<','<<initial.begin_ns<<','<<initial.end_ns<<'\n';
                    auto emit=[&](const NativeNetProposal& p,const NativeNetValidation& validation,unsigned attempt,bool committed){
                        tx<<rep<<','<<epoch<<','<<wave<<','<<slot<<','<<p.net<<','<<attempt<<','<<readCount<<','<<p.reads.size()<<','<<validation.conflicts.size()<<','<<validation.tree_changed<<','<<p.overflow<<','<<committed<<','<<p.expanded<<','<<p.edge_visits<<','<<p.quotient_expanded<<','<<p.quotient_edge_visits<<','<<p.max_labels<<','<<p.deferred_retries<<','<<p.label_packets<<','<<p.branches.size()<<','<<p.passes.size()<<'\n';
                        if(workerShadowSync){
                            shadowChecks<<rep<<','<<epoch<<','<<wave<<','<<slot<<','<<attempt<<','<<p.shadow_reads.size()<<','<<validation.stale_shadows.size()<<'\n';
                            for(size_t i=0;i<p.shadow_reads.size();++i){const auto& r=p.shadow_reads[i];shadowReads<<rep<<','<<epoch<<','<<wave<<','<<slot<<','<<attempt<<','<<i<<','<<r.branch<<','<<r.worker<<','<<r.node<<','<<r.seen.occupancy<<','<<r.seen.history<<','<<r.seen.version<<','<<r.hit<<'\n';}
                            for(size_t i=0;i<p.branches.size();++i)shadowBranches<<rep<<','<<epoch<<','<<wave<<','<<slot<<','<<attempt<<','<<i<<','<<p.branches[i].shadow_path<<'\n';
                            messages(p.shadow_messages,rep,epoch,wave,slot,attempt,0);
                        }
                        std::array<unsigned char,4096> buffer{};size_t used=0;
                        for(auto n:p.reads){auto u=p.snapshot->find_use(n);put32(buffer.data()+used,n);put32(buffer.data()+used+4,0);put64(buffer.data()+used+8,u?u->version:0);used+=16;
                            if(used==buffer.size()){readsets.append(buffer.data(),used);used=0;}}
                        if(used)readsets.append(buffer.data(),used);
                        readCount+=p.reads.size();
                        for(auto n:validation.conflicts){auto old=p.snapshot->find_use(n),now=state.find_use(n);conflicts<<rep<<','<<epoch<<','<<wave<<','<<slot<<','<<attempt<<','<<n<<','<<(old?old->version:0)<<','<<(now?now->version:0)<<'\n';}
                        for(size_t index=0;index<p.branches.size();++index){const auto& b=p.branches[index];const auto& r=b.result;
                            branches<<rep<<','<<epoch<<','<<wave<<','<<slot<<','<<attempt<<','<<index<<','<<b.task.id<<','<<p.net<<','<<b.task.sink<<','<<b.task.sink_die<<','<<b.pass<<','<<b.rescue<<','<<b.deferred<<','<<static_cast<int>(r.status)<<','<<r.attachment<<','<<r.hops<<','<<r.cost<<','<<r.expanded<<','<<r.edge_visits<<'\n';
                            auto from=r.attachment;for(size_t step=0;step<r.path.size();++step){branchPaths<<rep<<','<<epoch<<','<<wave<<','<<slot<<','<<attempt<<','<<index<<','<<step<<','<<from<<','<<r.path[step]<<','<<r.edges[step]<<'\n';from=r.path[step];}
                        }
                        for(const auto& pass:p.passes)passes<<rep<<','<<epoch<<','<<wave<<','<<slot<<','<<attempt<<','<<pass.pass<<','<<pass.before<<','<<pass.after<<','<<pass.failed<<','<<pass.deferred<<','<<pass.rescue<<','<<pass.retry<<'\n';
                        expanded+=p.expanded;visits+=p.edge_visits;qexpanded+=p.quotient_expanded;qvisits+=p.quotient_edge_visits;maxLabels=std::max(maxLabels,p.max_labels);deferred+=p.deferred_retries;
                    };
                    auto validation=validate(slot,initial,0);
                    bool committed=commit(slot,initial,validation,0);
                    emit(initial,validation,0,committed);
                    std::optional<NativeNetProposal> replay;
                    if(!committed){if(workerShadowSync)refresh(slot,epoch,wave,1,2);replay.emplace(execute(slot,initial.net,std::make_shared<const NativeRouteState>(state)));endpointTrace(rep,epoch,wave,slot,1,0);validation=validate(slot,*replay,1);
                        check(commit(slot,*replay,validation,1),"serial net replay invalidated");emit(*replay,validation,1,true);}
                    const auto& accepted=replay?*replay:initial;
                    for(auto [task,status]:accepted.statuses)statuses.at(task)=status;
                    acceptedExpanded+=accepted.expanded;acceptedVisits+=accepted.edge_visits;acceptedQexpanded+=accepted.quotient_expanded;acceptedQvisits+=accepted.quotient_edge_visits;
                    acceptedLabels=std::max(acceptedLabels,accepted.max_labels);acceptedDeferred+=accepted.deferred_retries;
                }
                ++shadowWindow;
                std::cout<<"repeat="<<rep<<" epoch="<<epoch<<" wave="<<wave<<" nets="<<batch.size()<<" expanded="<<expanded<<std::endl;
            }
            size_t routed=0;std::set<uint32_t> next;
            for(auto net:order)for(const auto& t:cohort.at(net)){if(statuses.at(t.id)==SparseSearchStatus::found)++routed;else next.insert(net);}
            auto overused=state.overused();logs<<rep<<','<<epoch<<','<<present<<','<<pending.size()<<','<<routed<<','<<(taskCount-routed)<<','<<overused<<','<<expanded<<','<<visits<<','<<qexpanded<<','<<qvisits<<','<<maxLabels<<','<<deferred<<'\n';logs.flush();
            acceptedWork<<rep<<','<<epoch<<','<<acceptedExpanded<<','<<acceptedVisits<<','<<acceptedQexpanded<<','<<acceptedQvisits<<','<<acceptedLabels<<','<<acceptedDeferred<<'\n';
            if(routed==taskCount&&!overused){++successfulRepeats;break;}
            if(epoch+1==iterations)break;
            std::set<uint32_t> congested;
            if(authority){if(present>UINT64_MAX/2)throw std::overflow_error("native present factor overflow");authority->context(rep,epoch,UINT32_MAX,UINT32_MAX,0);authority->negotiate(1,present*2);state=authority->snapshot();
                state.visit_uses([&](auto,const auto& u){if(u.nets.size()>1)congested.insert(u.nets.begin(),u.nets.end());});auto expected=oracle.negotiate(1);check(expected==congested,"net kernel congested set differs");NativeNetCommit::compare(state,oracle);check(authority->present()==present*2,"net kernel present differs");}
            else congested=state.negotiate(1);
            next.insert(congested.begin(),congested.end());pending=std::move(next);
            if(present>UINT64_MAX/2)throw std::overflow_error("native present factor overflow");
            present*=2;
        }
        if(fabric){publish(UINT32_MAX,shadowWindow,0);endpointTrace(rep,UINT32_MAX,shadowWindow,fabric->controller(),0,1);}
        if(workerShadowSync)for(size_t slot=0;slot<lanes.size();++slot)refresh(slot,UINT32_MAX,shadowWindow,0,3);
        if(fabric)fabric->inventory([&](auto owner,auto n,auto value){check(value==NativeWorkerShadows::authority(state,n),"HBM final owner mismatch");endpointOwners<<rep<<','<<owner<<','<<n<<','<<value.occupancy<<','<<value.history<<','<<value.version<<'\n';},
            [&](auto lane,auto worker,auto n,auto value){check(value==NativeWorkerShadows::authority(state,n),"HBM final cache mismatch");endpointCaches<<rep<<','<<lane<<','<<worker<<','<<n<<','<<value.occupancy<<','<<value.history<<','<<value.version<<'\n';});
        if(fabric)fabric->subscriptions([&](auto die,auto n,auto bits,auto pending,auto queued){endpointSubscriptions<<rep<<','<<die<<','<<n<<','<<bits<<','<<pending<<','<<queued<<'\n';});
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
    }
    if(authority)authority->finish();
    endpointFrames.finish_dynamic(384);endpointOwners.close();endpointCaches.close();check(bool(endpointOwners)&&bool(endpointCaches),"HBM inventory write");
    if(summaryHbm==2){endpointSubscriptions.close();check(bool(endpointSubscriptions),"HBM subscription inventory write");}
    readsets.finish_dynamic(16);shadowPackets.finish_dynamic(128);
    for(auto stream:{&shadowReads,&shadowChecks,&shadowBranches,&shadowPublications}){stream->close();check(bool(*stream),"persistent shadow output failure");}
    for(auto stream:{&logs,&connections,&paths,&treeOut,&usage,&ownerUsage,&tx,&branches,&branchPaths,&passes,&conflicts,&execution,&acceptedWork}){stream->close();check(bool(*stream),"parallel cohort output failure");}
    std::ofstream report(out/"audit.json");report<<"{\"schema\":\"dieroute.native_parallel_route.v1\",\"selected_seed_tasks\":"<<selectedTasks.size()<<",\"selected_nets\":"<<selected.size()<<",\"all_selected_net_tasks\":"<<taskCount<<",\"frozen_unselected_footprint_nodes\":"<<frozenCount<<",\"repeats\":"<<repeats<<",\"electrical_model_converged_repeats\":"<<successfulRepeats<<",\"native_design_legal\":null,\"net_workers\":"<<netWorkers<<",\"scope\":\""<<(authority?"CPU search with synthesizable whole-net authority, hardware-derived search snapshots and owner deltas; CPU oracle checked separately; no board or native QoR claim":"Parallel CPU whole-net proposals with fixed-order version validation and serial atomic publication; no asynchronous authority mutation, hardware or native QoR claim")<<"\"}\n";
    report.close();check(bool(report),"parallel report failure");return 0;
}catch(const std::exception& e){std::cerr<<"native_parallel: "<<e.what()<<'\n';return 1;}}
