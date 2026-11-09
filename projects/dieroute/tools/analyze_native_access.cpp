#include "native_csr_io.hpp"
#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <sstream>
#include <vector>
using namespace dieroute::native;
static std::vector<std::string> csv(const std::string& line){
    std::vector<std::string> result;std::stringstream input(line);std::string value;
    while(input>>std::quoted(value)){result.push_back(value);if(input.peek()==',')input.get();else break;}
    return result;
}
struct Component {uint32_t nodes=0,inputs=0,outputs=0,entries=0,exits=0;};
int main(int argc,char** argv){try{
    check(argc==6,"usage: analyze_native_access GRAPH MAPPING FOOTPRINT ARCH_FINGERPRINT NEW_OUTPUT");
    fs::path graph=argv[1],mapping=argv[2],footprint=argv[3],out=argv[5];auto arch=fingerprint(argv[4]);
    check(fs::create_directory(out),"output must be new");
    Raw nodes(graph/"nodes.bin",16),pips(graph/"pips.bin",8),nm(mapping/"footprint_node_map.bin",1),pm(mapping/"footprint_pip_map.bin",1),
        nets(footprint/"nets.bin",16),owners(footprint/"owners.bin",2),pins(footprint/"pins.bin",4),fp(footprint/"pips.bin",8);
    check(pm.count==fp.count,"PIP map coverage");
    std::ifstream tiles(graph/"tiles.csv");check(bool(tiles),"missing tile dictionary");std::string line;std::getline(tiles,line);
    std::map<uint32_t,std::string> tileTypes;uint32_t maxTile=0;
    while(std::getline(tiles,line)){auto cols=csv(line);check(cols.size()==9,"tile dictionary columns");auto id=uint32_t(std::stoul(cols[0]));
        check(tileTypes.emplace(id,cols[2]).second,"duplicate tile");maxTile=std::max(maxTile,id);}
    std::vector<unsigned char> tileCore(uint64_t(maxTile)+1,0),tileSeen(uint64_t(maxTile)+1,0);
    for(const auto& pair:tileTypes){tileSeen[pair.first]=1;tileCore[pair.first]=pair.second=="INT"||pair.second=="LAG_LAG"||pair.second=="LAGUNA_TILE";}
    std::vector<unsigned char> core(nodes.count,0);size_t coreNodes=0;
    for(size_t n=0;n<nodes.count;++n){auto tile=nodes.at(n,3);check(nodes.at(n,0)==n&&tile<tileSeen.size()&&tileSeen[tile],"native node tile identity");core[n]=tileCore[tile];coreNodes+=core[n];}
    auto mapped=[&](uint32_t old){check(old<nm.count,"node map bounds");auto n=nm.at(old,0);check(n<nodes.count,"mapped node bounds");return n;};
    std::ofstream comps(out/"components.csv"),exceptions(out/"nonterminal_components.csv");
    const char* header="net_id,component,nodes,input_pins,output_pins,core_entry_edges,core_exit_edges\n";comps<<header;exceptions<<header;
    std::vector<uint32_t> privateOwner(nodes.count,none);std::vector<std::array<uint32_t,4>> access;
    size_t candidateNets=0,candidatePips=0,corePips=0,noncorePips=0,privateNodes=0,componentCount=0,nonterminalComponents=0,transitComponents=0,
        sourceComponents=0,sinkComponents=0,mixedComponents=0,directComponents=0,multiEntry=0,multiExit=0,coreSourcePins=0,coreSinkPins=0,noncoreSourcePins=0,noncoreSinkPins=0;
    size_t maxNodes=0;std::map<std::string,size_t> noncoreTypes;
    for(size_t net=0;net<nets.count;++net){if(nets.at(net,0)!=0)continue;++candidateNets;
        size_t ob=nets.at(net,9),oc=nets.at(net,10),pb=nets.at(net,3),pc=nets.at(net,4),eb=nets.at(net,5),ec=nets.at(net,6);
        check(ob+oc<=owners.count&&pb+pc<=pins.count&&eb+ec<=fp.count,"net slice bounds");
        std::vector<uint32_t> old(oc),global(oc),parent(oc);std::iota(parent.begin(),parent.end(),0);
        for(size_t i=0;i<oc;++i){old[i]=owners.at(ob+i,0);check(owners.at(ob+i,1)==net&&(i==0||old[i]>old[i-1]),"net owner identity/order");global[i]=mapped(old[i]);
            if(!core[global[i]]){auto& owner=privateOwner[global[i]];check(owner==none||owner==net,"noncore node shared by candidate nets");
                if(owner==none){++privateNodes;++noncoreTypes[tileTypes.at(nodes.at(global[i],3))];}owner=net;}}
        auto local=[&](uint32_t id){auto it=std::lower_bound(old.begin(),old.end(),id);check(it!=old.end()&&*it==id,"pin/PIP absent from net ownership");return uint32_t(it-old.begin());};
        auto root=[&](uint32_t v){auto r=v;while(parent[r]!=r)r=parent[r];while(parent[v]!=v){auto next=parent[v];parent[v]=r;v=next;}return r;};
        std::vector<std::pair<uint32_t,uint32_t>> directed;
        for(size_t i=eb;i<eb+ec;++i){check(fp.at(i,0)==net,"PIP net mismatch");auto dir=fp.at(i,7)&1;
            auto a=local(fp.at(i,dir?2:1)),b=local(fp.at(i,dir?1:2));auto src=global[a],dst=global[b],id=pm.at(i,0);
            check(id<pips.count && src==pips.at(id,dir?2:1) && dst==pips.at(id,dir?1:2),"native PIP endpoint identity");
            check((pips.at(id,7)&2)||dir==(pips.at(id,7)&1),"native PIP direction");
            ++candidatePips;directed.push_back({a,b});
            if(core[src]&&core[dst])++corePips;
            else{++noncorePips;check(id<(1u<<31),"native edge key width");access.push_back({uint32_t(net),(id<<1)|dir,src,dst});}
            if(!core[src]&&!core[dst]){auto x=root(a),y=root(b);if(x!=y)parent[std::max(x,y)]=std::min(x,y);}
        }
        std::map<uint32_t,Component> components;
        for(size_t i=0;i<oc;++i)if(!core[global[i]])++components[root(i)].nodes;
        for(size_t i=pb;i<pb+pc;++i){check(pins.at(i,0)==net && pins.at(i,3)<=1,"pin identity/direction");auto id=local(pins.at(i,1));bool output=pins.at(i,3)!=0;
            if(core[global[id]]){if(output)++coreSourcePins;else ++coreSinkPins;}
            else{auto& c=components[root(id)];if(output){++c.outputs;++noncoreSourcePins;}else{++c.inputs;++noncoreSinkPins;}}}
        for(auto e:directed){auto a=global[e.first],b=global[e.second];
            if(core[a]&&!core[b])++components[root(e.second)].entries;
            if(!core[a]&&core[b])++components[root(e.first)].exits;}
        for(const auto& entry:components){const auto& c=entry.second;++componentCount;maxNodes=std::max(maxNodes,size_t(c.nodes));
            sourceComponents+=c.outputs>0&&c.inputs==0;sinkComponents+=c.inputs>0&&c.outputs==0;mixedComponents+=c.inputs>0&&c.outputs>0;
            directComponents+=c.entries==0&&c.exits==0;multiEntry+=c.entries>1;multiExit+=c.exits>1;
            auto emit=[&](std::ostream& s){s<<net<<','<<entry.first<<','<<c.nodes<<','<<c.inputs<<','<<c.outputs<<','<<c.entries<<','<<c.exits<<'\n';};emit(comps);
            if(!c.inputs&&!c.outputs){++nonterminalComponents;transitComponents+=c.entries>0&&c.exits>0;emit(exceptions);}
        }
        if(net%100000==0)std::cout<<"analyzed_net="<<net<<" private_nodes="<<privateNodes<<std::endl;
    }
    Writer coreOut(out/"core_nodes.bin",0x44520007,nodes.count,arch),ownerOut(out/"private_owner.bin",0x44520008,nodes.count,arch),accessOut(out/"access_arcs.bin",0x44520009,access.size(),arch);
    coreOut.append(core.data(),core.size());coreOut.finish(1);std::vector<unsigned char> block(1<<20);
    for(size_t start=0;start<nodes.count;){auto count=std::min(block.size()/4,nodes.count-start);for(size_t j=0;j<count;++j)put32(block.data()+4*j,privateOwner[start+j]);ownerOut.append(block.data(),count*4);start+=count;}ownerOut.finish(4);
    for(size_t start=0;start<access.size();){auto count=std::min(block.size()/16,access.size()-start);for(size_t j=0;j<count;++j)for(unsigned k=0;k<4;++k)put32(block.data()+16*j+4*k,access[start+j][k]);accessOut.append(block.data(),count*16);start+=count;}accessOut.finish(16);
    std::ofstream report(out/"audit.json");report<<"{\n  \"schema\":\"dieroute.native_access_analysis.v1\",\n  \"nodes\":"<<nodes.count<<",\n  \"core_nodes\":"<<coreNodes
        <<",\n  \"candidate_nets\":"<<candidateNets<<",\n  \"candidate_pips\":"<<candidatePips<<",\n  \"core_core_pips\":"<<corePips<<",\n  \"noncore_incident_pips\":"<<noncorePips
        <<",\n  \"candidate_private_noncore_nodes\":"<<privateNodes<<",\n  \"noncore_components\":"<<componentCount<<",\n  \"source_only_components\":"<<sourceComponents
        <<",\n  \"sink_only_components\":"<<sinkComponents<<",\n  \"mixed_terminal_components\":"<<mixedComponents<<",\n  \"no_core_boundary_components\":"<<directComponents
        <<",\n  \"nonterminal_components\":"<<nonterminalComponents<<",\n  \"nonterminal_transit_components\":"<<transitComponents<<",\n  \"multiple_core_entry_components\":"<<multiEntry
        <<",\n  \"multiple_core_exit_components\":"<<multiExit<<",\n  \"largest_noncore_component_nodes\":"<<maxNodes<<",\n  \"core_source_pins\":"<<coreSourcePins
        <<",\n  \"core_sink_pins\":"<<coreSinkPins<<",\n  \"noncore_source_pins\":"<<noncoreSourcePins<<",\n  \"noncore_sink_pins\":"<<noncoreSinkPins<<",\n  \"private_native_tile_types\": {";
    bool comma=false;for(const auto& pair:noncoreTypes){if(comma)report<<',';comma=true;report<<'"'<<pair.first<<"\":"<<pair.second;}
    report<<"},\n  \"scope\":\"original noncore component classification and exact directed PIP access inventory; not new routing or proof of unused site accessibility\"\n}\n";
    report.close();comps.close();exceptions.close();check(bool(report)&&bool(comps)&&bool(exceptions),"access audit output failed");
    std::cout<<"candidate_nets="<<candidateNets<<" noncore_pips="<<noncorePips<<" nonterminal_components="<<nonterminalComponents<<" transit_components="<<transitComponents<<std::endl;return 0;
}catch(const std::exception& e){std::cerr<<"native access failed: "<<e.what()<<std::endl;return 1;}}
