#include "native_csr_io.hpp"
#include "routing_policy.hpp"
#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <vector>
using namespace dieroute::native;
constexpr uint32_t policy_nodes_type=0x44520004,terminal_type=0x44520005,pip_policy_type=0x44520006;
int main(int argc,char** argv){try{
    check(argc==7,"usage: build_native_policy GRAPH MAPPING FOOTPRINT CSR ARCH_FINGERPRINT NEW_OUTPUT");
    fs::path graph=argv[1],mapping=argv[2],footprint=argv[3],csr=argv[4],out=argv[6];auto arch=fingerprint(argv[5]);
    check(fs::create_directory(out),"policy output must be new");
    Raw nodes(graph/"nodes.bin",16),pips(graph/"pips.bin",8),occupied(mapping/"occupied_nodes.bin",8),
        nm(mapping/"footprint_node_map.bin",1),pm(mapping/"footprint_pip_map.bin",1),
        nets(footprint/"nets.bin",16),pins(footprint/"pins.bin",4),fp(footprint/"pips.bin",8),tasks(footprint/"tasks.bin",8);
    Container inherited(csr/"protection.bin",protection_type,1,arch);
    check(inherited.count==nodes.count && pm.count==fp.count,"native policy table coverage");
    dieroute::RoutingPolicy policy;policy.node_protection.assign(nodes.count,0);policy.terminal_net.assign(nodes.count,none);
    // This file is indexed by native PIP catalog, not by CSR arc. Conversion to a
    // PR graph expands masks using edge_ref>>1, preserving parallel/directed arcs.
    policy.edge_protection.assign(pips.count,0);
    std::vector<unsigned char> occupiedSeen(nodes.count,0);std::vector<uint32_t> incoming(nodes.count,0);
    std::map<uint32_t,std::string> intents;std::ifstream names(graph/"intents.csv");check(bool(names),"missing intent dictionary");std::string line;
    std::getline(names,line);
    while(std::getline(names,line)){std::stringstream row(line);std::string id,name;char comma=0;row>>std::quoted(id)>>comma>>std::quoted(name);
        check(bool(row)&&comma==','&&!name.empty(),"invalid intent dictionary");
        check(intents.emplace(std::stoul(id),name).second,"duplicate intent ID");}
    for(size_t n=0;n<nodes.count;++n){check(nodes.at(n,0)==n,"native node ID");auto flags=nodes.at(n,8);
        check(!(flags&~7u),"unknown node flags");if(flags&3)policy.node_protection[n]|=4;if(flags&4)policy.node_protection[n]|=8;}
    for(size_t i=0;i<occupied.count;++i){auto n=occupied.at(i,0);check(n<nodes.count&&!occupiedSeen[n],"occupied node bounds/duplicate");occupiedSeen[n]=1;
        check(uint64_t(occupied.at(i,4))+occupied.at(i,5)==occupied.at(i,3),"occupied owner counts");
        if(occupied.at(i,4))policy.node_protection[n]|=1;
        if(occupied.at(i,6)&4)policy.node_protection[n]|=2;}
    size_t clockNodes=0,protectedNodes=0,terminalNodes=0;
    for(size_t n=0;n<nodes.count;++n){check(policy.node_protection[n]==inherited.data[n],"inherited protection disagrees with raw evidence");
        auto it=intents.find(nodes.at(n,7));check(it!=intents.end(),"unknown native intent ID");const auto& name=it->second;
        bool clock=name.rfind("NODE_GLOBAL_",0)==0 || name=="CLKPIN" || name=="GLOBAL" || name=="BUFGROUT" || name=="REFCLK";
        if(clock){policy.node_protection[n]|=16;++clockNodes;}protectedNodes+=policy.node_protection[n]!=0;}
    auto mapped=[&](uint32_t old){check(old<nm.count,"footprint node map bounds");auto n=nm.at(old,0);check(n<nodes.count,"mapped node bounds");return n;};
    auto candidate=[&](uint32_t net){check(net<nets.count,"footprint net bounds");return nets.at(net,0)==0;};
    size_t candidatePins=0,candidatePips=0,forbiddenPins=0,forbiddenPips=0;
    for(size_t i=0;i<pins.count;++i){auto net=pins.at(i,0);if(!candidate(net))continue;auto n=mapped(pins.at(i,1));++candidatePins;
        check(pins.at(i,2)<8&&(nodes.at(n,5)&(1u<<pins.at(i,2))),"pin access SLR outside node membership");
        auto& owner=policy.terminal_net[n];check(owner==none||owner==net,"terminal node shared by different candidate nets");
        if(owner==none)++terminalNodes;
        owner=net;forbiddenPins+=policy.node_protection[n]!=0;}
    size_t rawArcs=0,permittedArcs=0,deniedPips=0,deniedTerminalPairs=0,missingPips=0;
    for(size_t i=0;i<pips.count;++i){check(pips.at(i,0)==i,"native PIP ID");auto a=pips.at(i,1),b=pips.at(i,2),flags=pips.at(i,7);
        check(!(flags&~255u),"unknown native PIP flags");auto& mask=policy.edge_protection[i];mask=flags&(4|8|16|32|128);
        check((a==none||a<nodes.count)&&(b==none||b<nodes.count),"native PIP endpoint bounds");
        if(a==none||b==none){mask|=128;++missingPips;}deniedPips+=mask!=0;
        if(a==none||b==none)continue;
        auto direction=[&](uint32_t src,uint32_t dst){++rawArcs;check(incoming[dst]!=none,"incoming degree overflow");++incoming[dst];
            if(mask||policy.node_protection[src]||policy.node_protection[dst])return;
            auto x=policy.terminal_net[src],y=policy.terminal_net[dst];
            if(x!=none&&y!=none&&x!=y){++deniedTerminalPairs;return;}++permittedArcs;};
        if(flags&2){direction(a,b);direction(b,a);}else if(flags&1)direction(b,a);else direction(a,b);
        if(i%100000000==0)std::cout<<"classified_native_pips="<<i<<std::endl;
    }
    std::ofstream rejected(out/"forbidden_candidate_pips.csv");rejected<<"footprint_pip_id,net_id,native_pip_id,source,destination,source_mask,destination_mask,pip_mask\n";
    for(size_t i=0;i<fp.count;++i){auto net=fp.at(i,0);if(!candidate(net))continue;++candidatePips;
        auto id=pm.at(i,0);check(id<pips.count,"mapped PIP bounds");auto dir=fp.at(i,7)&1;
        auto src=mapped(fp.at(i,dir?2:1)),dst=mapped(fp.at(i,dir?1:2));auto flags=pips.at(id,7);
        check(src==pips.at(id,dir?2:1)&&dst==pips.at(id,dir?1:2),"original PIP endpoint map mismatch");
        check((flags&2)||dir==(flags&1),"original PIP direction mismatch");
        if(!policy.node_allowed(src,net)||!policy.node_allowed(dst,net)||!policy.edge_allowed(id)){
            if(forbiddenPips++<64)rejected<<i<<','<<net<<','<<id<<','<<src<<','<<dst<<','<<unsigned(policy.node_protection[src])<<','<<unsigned(policy.node_protection[dst])<<','<<unsigned(policy.edge_protection[id])<<'\n';}
    }
    size_t multiSource=0,multiSink=0,sourcesWithIncoming=0,cross=0,forbiddenTasks=0;std::vector<unsigned char> seenSource(nodes.count,0);
    for(size_t i=0;i<tasks.count;++i){check(tasks.at(i,0)==i,"task ID");auto net=tasks.at(i,1),src=mapped(tasks.at(i,2)),dst=mapped(tasks.at(i,3));
        check(candidate(net)&&policy.terminal_net[src]==net&&policy.terminal_net[dst]==net,"task does not resolve to its net terminals");
        for(unsigned terminal=0;terminal<2;++terminal){auto pin=tasks.at(i,6+terminal),node=terminal?dst:src,die=tasks.at(i,4+terminal);
            check(pin<pins.count&&pins.at(pin,0)==net&&mapped(pins.at(pin,1))==node&&pins.at(pin,2)==die&&pins.at(pin,3)==(terminal?0u:1u),"task pin identity/access mismatch");}
        if(!seenSource[src]){seenSource[src]=1;sourcesWithIncoming+=incoming[src]!=0;multiSource+=(nodes.at(src,5)&(nodes.at(src,5)-1))!=0;}
        multiSink+=(nodes.at(dst,5)&(nodes.at(dst,5)-1))!=0;cross+=tasks.at(i,4)!=tasks.at(i,5);
        forbiddenTasks+=!policy.node_allowed(src,net)||!policy.node_allowed(dst,net);
    }
    Writer ns(out/"node_protection.bin",policy_nodes_type,nodes.count,arch),ts(out/"terminal_net.bin",terminal_type,nodes.count,arch),ps(out/"pip_protection.bin",pip_policy_type,pips.count,arch);
    ns.append(policy.node_protection.data(),policy.node_protection.size());ns.finish(1);
    ps.append(policy.edge_protection.data(),policy.edge_protection.size());ps.finish(1);
    std::vector<unsigned char> block(1<<20);
    for(size_t start=0;start<nodes.count;){auto count=std::min(block.size()/4,nodes.count-start);for(size_t i=0;i<count;++i)put32(block.data()+4*i,policy.terminal_net[start+i]);ts.append(block.data(),count*4);start+=count;}ts.finish(4);
    bool passed=!forbiddenPins&&!forbiddenPips&&!forbiddenTasks;
    std::ofstream report(out/"audit.json");report<<"{\n  \"schema\":\"dieroute.native_policy.v1\",\n  \"original_candidate_footprint_preserved\":"<<(passed?"true":"false")
        <<",\n  \"nodes\":"<<nodes.count<<",\n  \"pips\":"<<pips.count<<",\n  \"raw_arcs\":"<<rawArcs<<",\n  \"policy_permitted_arcs_before_net_specific_checks\":"<<permittedArcs
        <<",\n  \"protected_nodes\":"<<protectedNodes<<",\n  \"clock_intent_nodes\":"<<clockNodes<<",\n  \"restricted_native_pips\":"<<deniedPips<<",\n  \"missing_endpoint_pips\":"<<missingPips
        <<",\n  \"different_terminal_owner_arcs\":"<<deniedTerminalPairs<<",\n  \"exclusive_candidate_pin_nodes\":"<<terminalNodes<<",\n  \"candidate_pins_checked\":"<<candidatePins
        <<",\n  \"candidate_pips_checked\":"<<candidatePips<<",\n  \"candidate_tasks_checked\":"<<tasks.count<<",\n  \"forbidden_candidate_pins\":"<<forbiddenPins<<",\n  \"forbidden_candidate_pips\":"<<forbiddenPips
        <<",\n  \"forbidden_candidate_tasks\":"<<forbiddenTasks<<",\n  \"candidate_source_nodes_with_incoming_arcs\":"<<sourcesWithIncoming
        <<",\n  \"multi_slr_source_nodes\":"<<multiSource<<",\n  \"multi_slr_sink_tasks\":"<<multiSink<<",\n  \"cross_slr_tasks\":"<<cross
        <<",\n  \"scope\":\"immutable resource/clock/PIP/terminal constraints and original path preservation only; not full site/tile legality, capacity/delay calibration or new commercial routing\"\n}\n";
    report.close();rejected.close();check(bool(report)&&bool(rejected),"policy audit write failed");
    std::cout<<"candidate_footprint_preserved="<<passed<<" protected_nodes="<<protectedNodes<<" policy_permitted_arcs="<<permittedArcs<<std::endl;
    return passed?0:3;
}catch(const std::exception& e){std::cerr<<"native policy failed: "<<e.what()<<std::endl;return 1;}}
