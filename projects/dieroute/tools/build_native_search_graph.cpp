#include "native_csr_io.hpp"
#include <algorithm>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <vector>
using namespace dieroute::native;
// Keep original physical node IDs. This is qualified adjacency for fixed pin
// access, not a cost model, PR-state allocation, or a completed rerouting run.
int main(int argc,char** argv){try{
    check(argc==9,"usage: build_native_search_graph GRAPH MAPPING FOOTPRINT CSR POLICY ACCESS ARCH_FINGERPRINT NEW_OUTPUT");
    fs::path graph=argv[1],mapping=argv[2],footprint=argv[3],csr=argv[4],policy=argv[5],access=argv[6],out=argv[8];auto arch=fingerprint(argv[7]);
    check(fs::create_directory(out),"output must be new");
    Raw nodes(graph/"nodes.bin",16),nets(footprint/"nets.bin",16),fp(footprint/"pips.bin",8),nm(mapping/"footprint_node_map.bin",1),pm(mapping/"footprint_pip_map.bin",1);
    Container offsets(csr/"offsets.bin",offsets_type,8,arch),arcs(csr/"arcs.bin",arcs_type,8,arch),
        baseMasks(policy/"node_protection.bin",0x44520004,1,arch),baseOwners(policy/"terminal_net.bin",0x44520005,4,arch),pipMasks(policy/"pip_protection.bin",0x44520006,1,arch),
        core(access/"core_nodes.bin",0x44520007,1,arch),privateOwners(access/"private_owner.bin",0x44520008,4,arch),accessArcs(access/"access_arcs.bin",0x44520009,16,arch);
    check(offsets.count==nodes.count+1&&baseMasks.count==nodes.count&&baseOwners.count==nodes.count&&core.count==nodes.count&&privateOwners.count==nodes.count,"node table coverage");
    check(nodes.count<none&&pipMasks.count<=uint64_t(1)<<31,"native graph identity width");
    check(pm.count==fp.count&&offsets.offset(0)==0&&offsets.offset(nodes.count)==arcs.count,"CSR/PIP map coverage");
    // Explicitly reject a design containing nonterminal noncore transit islands.
    std::ifstream nonterminal(access/"nonterminal_components.csv");check(bool(nonterminal),"missing nonterminal component audit");std::string line;
    check(bool(std::getline(nonterminal,line)),"missing nonterminal audit header");
    while(std::getline(nonterminal,line))check(line.empty(),"nonterminal noncore component needs a separate routing model");
    std::vector<unsigned char> masks(baseMasks.data,baseMasks.data+nodes.count),preLaguna(nodes.count,0),lagunaInput(nodes.count,0);
    std::vector<uint32_t> owners(nodes.count,none),accessKeys;accessKeys.reserve(accessArcs.count);
    std::vector<std::array<uint32_t,4>> expectedAccess,actualAccess;
    for(size_t i=0;i<fp.count;++i){auto net=fp.at(i,0);check(net<nets.count,"footprint net bounds");if(nets.at(net,0)!=0)continue;
        auto dir=fp.at(i,7)&1,a=fp.at(i,dir?2:1),b=fp.at(i,dir?1:2),id=pm.at(i,0);check(a<nm.count&&b<nm.count&&id<pipMasks.count,"original access map bounds");
        auto src=nm.at(a,0),dst=nm.at(b,0);check(src<nodes.count&&dst<nodes.count,"original access node bounds");
        if(!core.data[src]||!core.data[dst])expectedAccess.push_back({net,(id<<1)|dir,src,dst});}
    size_t privateCount=0,newProjected=0,lagunaInputs=0,pinfeedsBlocked=0,noncoreBlocked=0;
    for(size_t n=0;n<nodes.count;++n){check(core.data[n]<=1,"core class must be boolean");owners[n]=le32(baseOwners.data+4*n);auto other=le32(privateOwners.data+4*n);
        if(other!=none){check(!core.data[n]&&(owners[n]==none||owners[n]==other),"private/core/terminal owner disagreement");owners[n]=other;++privateCount;}
        if(!core.data[n]&&other==none){masks[n]|=32;++noncoreBlocked;}}
    for(size_t i=0;i<accessArcs.count;++i){const auto* r=accessArcs.data+16*i;auto net=le32(r),key=le32(r+4),src=le32(r+8),dst=le32(r+12);
        actualAccess.push_back({net,key,src,dst});
        check(net<nets.count&&nets.at(net,0)==0&&src<nodes.count&&dst<nodes.count&&(key>>1)<pipMasks.count,"access arc bounds/net");
        check(!(core.data[src]&&core.data[dst])&&!masks[src]&&!masks[dst]&&!pipMasks.data[key>>1],"original access violates existing hard admission");
        check((core.data[src]||owners[src]==net)&&(core.data[dst]||owners[dst]==net),"access arc outside its private owner");
        // A sink's original first core node is its fixed projection. Each sink
        // component has exactly one entering edge in the frozen DCP analysis.
        if(core.data[src]&&!core.data[dst]){check(owners[src]==none||owners[src]==net,"projected sink is owned by another net");if(owners[src]==none)++newProjected;owners[src]=net;}
        accessKeys.push_back(key);
        auto lo=offsets.offset(src),end=offsets.offset(src+1),hi=end;check(lo<=end&&end<=arcs.count,"CSR range");auto want=std::make_pair(dst,key);
        while(lo<hi){auto mid=lo+(hi-lo)/2;if(std::make_pair(arcs.dst(mid),arcs.edge(mid))<want)lo=mid+1;else hi=mid;}
        check(lo<end&&std::make_pair(arcs.dst(lo),arcs.edge(lo))==want,"access PIP direction absent from raw CSR");
    }
    std::sort(expectedAccess.begin(),expectedAccess.end());std::sort(actualAccess.begin(),actualAccess.end());
    check(expectedAccess==actualAccess,"access inventory differs from original candidate PIPs");
    std::sort(accessKeys.begin(),accessKeys.end());check(std::adjacent_find(accessKeys.begin(),accessKeys.end())==accessKeys.end(),"duplicate access PIP direction");
    // The native graph's intent dictionary is fixed by the parent manifest:
    // NODE_PINFEED=6, NODE_LAGUNA_DATA=19. Refuse incompatible dictionaries.
    std::ifstream intents(graph/"intents.csv");check(bool(intents),"missing intent dictionary");std::string dictionary((std::istreambuf_iterator<char>(intents)),{});
    check(dictionary.find("\"6\",\"NODE_PINFEED\"")!=std::string::npos&&dictionary.find("\"19\",\"NODE_LAGUNA_DATA\"")!=std::string::npos,"unsupported native intent IDs");
    std::ifstream tileFile(graph/"tiles.csv");check(bool(tileFile),"missing tile dictionary");std::getline(tileFile,line);std::vector<unsigned char> tileClass;
    while(std::getline(tileFile,line)){std::stringstream row(line);std::string address,name,type;char comma=0;
        row>>std::quoted(address)>>comma>>std::quoted(name)>>comma>>std::quoted(type);check(bool(row)&&comma==',',"invalid tile row");auto id=std::stoul(address);
        if(tileClass.size()<=id)tileClass.resize(id+1,255);
        check(tileClass[id]==255,"duplicate tile address");tileClass[id]=type=="INT"?1:(type=="LAG_LAG"||type=="LAGUNA_TILE"?2:0);}
    for(size_t n=0;n<nodes.count;++n){auto tile=nodes.at(n,3);check(tile<tileClass.size()&&tileClass[tile]!=255,"native tile bounds");
        check(core.data[n]==(tileClass[tile]!=0),"core class disagrees with native tile type");}
    for(size_t src=0;src<nodes.count;++src){auto begin=offsets.offset(src),end=offsets.offset(src+1);check(begin<=end&&end<=arcs.count,"CSR monotonicity");
        for(auto i=begin;i<end;++i){auto dst=arcs.dst(i);check(dst<nodes.count&&(arcs.edge(i)>>1)<pipMasks.count,"raw arc bounds");
            // Include device-edge UBUMPs with only one SLR membership too.
            // The independent SDK export verifies this intent class exactly.
            if(nodes.at(dst,7)==19)preLaguna[src]=1;}}
    for(size_t src=0;src<nodes.count;++src)if(core.data[src]&&nodes.at(src,7)==6){
        if(tileClass[nodes.at(src,3)]==1)for(auto i=offsets.offset(src);i<offsets.offset(src+1);++i)if(preLaguna[arcs.dst(i)]){lagunaInput[src]=1;break;}
        lagunaInputs+=lagunaInput[src]!=0;
        if(owners[src]==none&&!lagunaInput[src]){masks[src]|=64;++pinfeedsBlocked;}}
    std::vector<uint64_t> selectedOffsets(nodes.count+1,0);size_t keptCore=0,keptAccess=0,ownerConflicts=0,missingAccess=0;
    auto permitted=[&](uint32_t src,size_t i){auto dst=arcs.dst(i),key=arcs.edge(i);
        if(masks[src]||masks[dst]||pipMasks.data[key>>1])return false;
        if(owners[src]!=none&&owners[dst]!=none&&owners[src]!=owners[dst])return false;
        return (core.data[src]&&core.data[dst])||std::binary_search(accessKeys.begin(),accessKeys.end(),key);};
    for(size_t src=0;src<nodes.count;++src){
        if(!masks[src])for(auto i=offsets.offset(src);i<offsets.offset(src+1);++i){auto dst=arcs.dst(i),key=arcs.edge(i);
            if(!masks[dst]&&!pipMasks.data[key>>1]&&owners[src]!=none&&owners[dst]!=none&&owners[src]!=owners[dst])++ownerConflicts;
            if(permitted(src,i)){++selectedOffsets[src+1];if(core.data[src]&&core.data[dst])++keptCore;else ++keptAccess;}}
        selectedOffsets[src+1]+=selectedOffsets[src];}
    check(keptAccess==accessKeys.size(),"fixed access arc lost during qualification");
    Writer oo(out/"offsets.bin",offsets_type,selectedOffsets.size(),arch),ao(out/"arcs.bin",arcs_type,selectedOffsets.back(),arch),
        mo(out/"node_protection.bin",0x4452000a,nodes.count,arch),to(out/"exclusive_net.bin",0x4452000b,nodes.count,arch),li(out/"laguna_input.bin",0x4452000c,nodes.count,arch);
    std::vector<unsigned char> block(1<<20);size_t used=0;
    for(size_t src=0;src<nodes.count;++src)if(!masks[src])for(auto i=offsets.offset(src);i<offsets.offset(src+1);++i)if(permitted(src,i)){
        put32(block.data()+used,arcs.dst(i));put32(block.data()+used+4,arcs.edge(i));used+=8;
        if(used==block.size()){ao.append(block.data(),used);used=0;}}
    if(used)ao.append(block.data(),used);
    ao.finish(8);
    for(size_t start=0;start<selectedOffsets.size();){auto len=std::min(block.size()/8,selectedOffsets.size()-start);for(size_t j=0;j<len;++j)put64(block.data()+8*j,selectedOffsets[start+j]);oo.append(block.data(),len*8);start+=len;}oo.finish(8);
    mo.append(masks.data(),masks.size());mo.finish(1);li.append(lagunaInput.data(),lagunaInput.size());li.finish(1);
    for(size_t start=0;start<owners.size();){auto len=std::min(block.size()/4,owners.size()-start);for(size_t j=0;j<len;++j)put32(block.data()+4*j,owners[start+j]);to.append(block.data(),len*4);start+=len;}to.finish(4);
    // Every original candidate PIP must remain with the exact selected direction.
    Container filtered(out/"arcs.bin",arcs_type,8,arch);size_t candidates=0;
    std::ofstream lost(out/"lost_candidate_pips.csv");lost<<"footprint_pip,net,source,destination,pip_key\n";
    for(size_t i=0;i<fp.count;++i){auto net=fp.at(i,0);check(net<nets.count,"footprint net bounds");if(nets.at(net,0)!=0)continue;++candidates;
        auto dir=fp.at(i,7)&1;auto a=fp.at(i,dir?2:1),b=fp.at(i,dir?1:2);check(a<nm.count&&b<nm.count,"footprint node map bounds");
        auto src=nm.at(a,0),dst=nm.at(b,0),id=pm.at(i,0);check(src<nodes.count&&dst<nodes.count&&id<pipMasks.count&&id<(1u<<31),"original PIP bounds");auto key=(id<<1)|dir;
        auto lo=selectedOffsets[src],end=selectedOffsets[src+1],hi=end;auto want=std::make_pair(dst,key);
        while(lo<hi){auto mid=lo+(hi-lo)/2;if(std::make_pair(filtered.dst(mid),filtered.edge(mid))<want)lo=mid+1;else hi=mid;}
        bool ownerOK=(owners[src]==none||owners[src]==net)&&(owners[dst]==none||owners[dst]==net);
        if(lo==end||std::make_pair(filtered.dst(lo),filtered.edge(lo))!=want||!ownerOK){if(missingAccess++<64)lost<<i<<','<<net<<','<<src<<','<<dst<<','<<key<<'\n';}
    }
    size_t blocked=0,exclusive=0;for(size_t n=0;n<nodes.count;++n){blocked+=masks[n]!=0;exclusive+=owners[n]!=none;}
    std::ofstream report(out/"audit.json");report<<"{\n  \"schema\":\"dieroute.native_search_graph.v1\",\n  \"original_candidate_pips_preserved\":"<<(missingAccess?"false":"true")
        <<",\n  \"nodes\":"<<nodes.count<<",\n  \"raw_arcs\":"<<arcs.count<<",\n  \"search_arcs\":"<<filtered.count<<",\n  \"core_core_arcs\":"<<keptCore<<",\n  \"fixed_access_arcs\":"<<keptAccess
        <<",\n  \"private_noncore_nodes\":"<<privateCount<<",\n  \"new_projected_sink_nodes\":"<<newProjected<<",\n  \"laguna_pinfeed_nodes\":"<<lagunaInputs
        <<",\n  \"unused_pinfeed_nodes_blocked\":"<<pinfeedsBlocked<<",\n  \"unused_noncore_nodes_blocked\":"<<noncoreBlocked<<",\n  \"all_blocked_nodes\":"<<blocked
        <<",\n  \"exclusive_net_nodes\":"<<exclusive<<",\n  \"foreign_terminal_owner_arcs_removed\":"<<ownerConflicts<<",\n  \"candidate_pips_checked\":"<<candidates
        <<",\n  \"missing_candidate_pips\":"<<missingAccess<<",\n  \"scope\":\"fixed existing pin-access choices plus INT/Laguna search adjacency; no alternate site/pin swaps, delay/capacity calibration, full rerouting or native legality/QoR claim\"\n}\n";
    report.close();lost.close();check(bool(report)&&bool(lost),"search graph audit output failed");
    std::cout<<"search_arcs="<<filtered.count<<" original_candidate_pips="<<candidates<<" missing="<<missingAccess<<std::endl;return missingAccess?3:0;
}catch(const std::exception& e){std::cerr<<"native search graph failed: "<<e.what()<<std::endl;return 1;}}
