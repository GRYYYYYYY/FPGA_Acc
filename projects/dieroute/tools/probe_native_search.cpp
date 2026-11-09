#include "native_csr_io.hpp"
#include "sparse_search.hpp"
#include "native_quotient.hpp"
#include <iostream>
#include <memory>
#include <map>
#include <set>
using namespace dieroute;
using namespace dieroute::native;
// Full graph consumer for connectivity/memory diagnostics. Unit increment is
// explicitly hop count, never physical delay, congestion cost or FPGA timing.
int main(int argc,char** argv){try{
    check(argc>=10&&argc<=12,"usage: probe_native_search GRAPH SEARCH FOOTPRINT MAPPING ARCH NEW_OUTPUT LABEL_LIMIT TASKS_PER_SLR_PAIR REPEATS [QUOTIENT [source_radius]]");
    if(argc==12)check(std::string(argv[11])=="source_radius","unknown quotient radius mode");
    fs::path graph=argv[1],search=argv[2],footprint=argv[3],mapping=argv[4],out=argv[6];auto arch=fingerprint(argv[5]);
    auto limit=std::stoull(argv[7]),take=std::stoull(argv[8]),repeats=std::stoull(argv[9]);check(limit&&take&&repeats,"positive probe limits required");
    check(fs::create_directory(out),"new output directory required");
    Container offsets(search/"offsets.bin",offsets_type,8,arch),arcs(search/"arcs.bin",arcs_type,8,arch),
        mask(search/"node_protection.bin",0x4452000a,1,arch),owner(search/"exclusive_net.bin",0x4452000b,4,arch);
    Raw tasks(footprint/"tasks.bin",8),nodeMap(mapping/"footprint_node_map.bin",1),nodes(graph/"nodes.bin",16);
    check(nodes.count<UINT32_MAX&&mask.count==nodes.count&&owner.count==nodes.count&&offsets.count==nodes.count+1,"node coverage");
    check(offsets.offset(0)==0&&offsets.offset(nodes.count)==arcs.count,"CSR coverage");
    std::map<std::pair<uint32_t,uint32_t>,size_t> pairCounts;std::vector<size_t> selected;
    for(size_t i=0;i<tasks.count;++i){check(tasks.at(i,0)==i,"task ID");auto pair=std::make_pair(tasks.at(i,4),tasks.at(i,5));
        if(pairCounts[pair]++<take)selected.push_back(i);}
    std::ofstream results(out/"results.csv"),paths(out/"paths.csv");
    results<<"repeat,task,net,source,sink,source_slr,sink_slr,status,hops,expanded,edge_visits,touched,workspace_bytes,lower_bound,quotient_expanded,quotient_edge_visits,quotient_workspace_bytes\n";
    paths<<"repeat,task,step,source,destination,pip_key\n";
    auto mapped=[&](uint32_t old){check(old<nodeMap.count,"footprint node bounds");auto n=nodeMap.at(old,0);check(n<nodes.count,"mapped node bounds");return n;};
    SparseSearch workspace;size_t found=0,limited=0,exhausted=0,maxTouched=0,maxBytes=0;
    std::unique_ptr<QuotientPotential> potential;if(argc>=11)potential=std::make_unique<QuotientPotential>(argv[10],arch,nodes.count);
    for(size_t rep=0;rep<repeats;++rep)for(auto task:selected){auto net=tasks.at(task,1),src=mapped(tasks.at(task,2)),dst=mapped(tasks.at(task,3));
        auto allowed=[&](uint32_t n){return !mask.data[n]&&(le32(owner.data+4*n)==none||le32(owner.data+4*n)==net);};
        check(allowed(src)&&allowed(dst),"forbidden task endpoint");
        if(potential)potential->prepare(dst,argc==12?src:none);
        auto r=workspace.run_guided(nodes.count,{{src,0,0}},dst,UINT32_MAX,[&](uint32_t n,auto offer){
            auto begin=offsets.offset(n),end=offsets.offset(n+1);check(begin<=end&&end<=arcs.count,"CSR row bounds");
            for(auto edge=begin;edge<end;++edge){auto to=arcs.dst(edge);check(to<nodes.count,"CSR destination bounds");
                if(allowed(to))offer(to,arcs.edge(edge),[](){return std::optional<uint64_t>(1);});}
        },[&](uint32_t n){return potential?(*potential)(n):uint64_t(0);},{size_t(limit),UINT64_MAX});
        const char* status=nullptr;
        if(r.status==SparseSearchStatus::found){status="found";++found;check(r.attachment==src&&r.cost==r.path.size(),"hop diagnostic path");
            auto from=src;for(size_t step=0;step<r.path.size();++step){auto to=r.path[step];check(allowed(to),"path net permission");
                paths<<rep<<','<<task<<','<<step<<','<<from<<','<<to<<','<<r.edges[step]<<'\n';from=to;}check(from==dst,"path endpoint");}
        else if(r.status==SparseSearchStatus::budget_exhausted){status="budget_exhausted";++limited;}
        else {check(r.status==SparseSearchStatus::exhausted,"unexpected hop cutoff");status="exhausted";++exhausted;}
        maxTouched=std::max(maxTouched,workspace.touched());maxBytes=std::max(maxBytes,workspace.retained_bytes());
        results<<rep<<','<<task<<','<<net<<','<<src<<','<<dst<<','<<tasks.at(task,4)<<','<<tasks.at(task,5)<<','<<status<<','<<r.hops<<','<<r.expanded<<','<<r.edge_visits<<','<<workspace.touched()<<','<<workspace.retained_bytes()<<','<<(potential?(*potential)(src):0)<<','<<(potential?potential->expanded:0)<<','<<(potential?potential->edge_visits:0)<<','<<(potential?potential->retained_bytes():0)<<'\n';
        std::cout<<"repeat="<<rep<<" task="<<task<<" status="<<status<<" expanded="<<r.expanded<<" touched="<<workspace.touched()<<std::endl;
    }
    results.close();paths.close();check(bool(results)&&bool(paths),"probe output failure");
    std::ofstream report(out/"audit.json");report<<"{\"schema\":\"dieroute.native_sparse_search_probe.v1\",\"nodes\":"<<nodes.count<<",\"arcs\":"<<arcs.count
        <<",\"selected_tasks\":"<<selected.size()<<",\"slr_pairs\":"<<pairCounts.size()<<",\"repeats\":"<<repeats<<",\"found\":"<<found<<",\"budget_exhausted\":"<<limited
        <<",\"exhausted\":"<<exhausted<<",\"maximum_touched_labels\":"<<maxTouched<<",\"maximum_retained_workspace_bytes\":"<<maxBytes<<",\"quotient_guidance\":"<<(potential?"true":"false")<<",\"source_radius\":"<<(argc==12?"true":"false")
        <<",\"scope\":\"full native CSR shortest-hop connectivity probes with net permission and sparse labels; budget exhaustion is inconclusive, not unroutable; no occupancy negotiation, physical costs, full-design routing or QoR\"}\n";
    report.close();check(bool(report),"audit write failure");return exhausted?3:0;
}catch(const std::exception& e){std::cerr<<"native search probe failed: "<<e.what()<<std::endl;return 1;}}
