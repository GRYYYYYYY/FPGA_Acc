#include "native_csr_io.hpp"
#include <algorithm>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using namespace dieroute::native;
struct Access {uint32_t net,src,dst;};
int main(int argc,char** argv){try{
    check(argc==11,"usage: verify_native_search_graph GRAPH MAPPING FOOTPRINT CSR POLICY ACCESS SEARCH SDK_INPUTS ARCH_FINGERPRINT NEW_OUTPUT");
    fs::path graph=argv[1],mapping=argv[2],footprint=argv[3],csr=argv[4],policy=argv[5],access=argv[6],search=argv[7],out=argv[10];auto arch=fingerprint(argv[9]);
    check(fs::create_directory(out),"output must be new");
    Raw nodes(graph/"nodes.bin",16),nets(footprint/"nets.bin",16),fp(footprint/"pips.bin",8),pins(footprint/"pins.bin",4),nm(mapping/"footprint_node_map.bin",1),pm(mapping/"footprint_pip_map.bin",1),sdk(argv[8],2);
    Container ro(csr/"offsets.bin",offsets_type,8,arch),ra(csr/"arcs.bin",arcs_type,8,arch),fo(search/"offsets.bin",offsets_type,8,arch),fa(search/"arcs.bin",arcs_type,8,arch),
        baseMask(policy/"node_protection.bin",0x44520004,1,arch),baseOwner(policy/"terminal_net.bin",0x44520005,4,arch),pipMask(policy/"pip_protection.bin",0x44520006,1,arch),
        core(access/"core_nodes.bin",0x44520007,1,arch),privateOwner(access/"private_owner.bin",0x44520008,4,arch),
        mask(search/"node_protection.bin",0x4452000a,1,arch),owner(search/"exclusive_net.bin",0x4452000b,4,arch),laguna(search/"laguna_input.bin",0x4452000c,1,arch);
    check(ro.count==nodes.count+1&&fo.count==nodes.count+1&&ro.offset(0)==0&&fo.offset(0)==0&&ro.offset(nodes.count)==ra.count&&fo.offset(nodes.count)==fa.count,"CSR coverage");
    for(const auto* c:{&baseMask,&baseOwner,&core,&privateOwner,&mask,&owner,&laguna})check(c->count==nodes.count,"node table coverage");
    check(pm.count==fp.count,"PIP map coverage");
    std::ifstream tf(graph/"tiles.csv");check(bool(tf),"missing tile dictionary");std::string line;std::getline(tf,line);std::vector<unsigned char> tileClass;
    while(std::getline(tf,line)){std::stringstream row(line);std::string id,name,type;char comma=0;row>>std::quoted(id)>>comma>>std::quoted(name)>>comma>>std::quoted(type);check(bool(row)&&comma==',',"tile row");auto n=std::stoul(id);
        if(tileClass.size()<=n)tileClass.resize(n+1,255);
        check(tileClass[n]==255,"duplicate tile ID");tileClass[n]=type=="INT"?1:(type=="LAG_LAG"||type=="LAGUNA_TILE"?2:0);}
    Raw sdkUbump(fs::path(argv[8]).parent_path()/"ubump_nodes.bin",2);
    std::unordered_set<uint64_t> sdkKeys,sdkRootKeys;uint64_t previous=0;
    for(size_t i=0;i<sdk.count;++i){auto key=(uint64_t(sdk.at(i,0))<<32)|sdk.at(i,1);check(i==0||key>previous,"SDK input ordering/duplicate");previous=key;sdkKeys.insert(key);}
    for(size_t i=0;i<sdkUbump.count;++i){auto key=(uint64_t(sdkUbump.at(i,0))<<32)|sdkUbump.at(i,1);check(i==0||key>previous,"SDK UBUMP ordering/duplicate");previous=key;sdkRootKeys.insert(key);}
    std::vector<uint32_t> expectedOwner(nodes.count,none);std::vector<unsigned char> usedNoncore(nodes.count,0),expectedMask(nodes.count,0);
    for(size_t n=0;n<nodes.count;++n){auto tile=nodes.at(n,3);check(tile<tileClass.size()&&tileClass[tile]!=255&&core.data[n]==(tileClass[tile]!=0),"core native tile classification");expectedOwner[n]=le32(baseOwner.data+4*n);}
    auto mapped=[&](uint32_t old){check(old<nm.count,"old node bounds");auto n=nm.at(old,0);check(n<nodes.count,"mapped node bounds");return n;};
    auto claim=[&](uint32_t n,uint32_t net){check(expectedOwner[n]==none||expectedOwner[n]==net,"conflicting private/projected owner");expectedOwner[n]=net;};
    std::unordered_map<uint32_t,Access> originalAccess;size_t candidatePips=0;
    for(size_t i=0;i<pins.count;++i){auto net=pins.at(i,0);check(net<nets.count,"pin net bounds");if(nets.at(net,0)!=0)continue;auto n=mapped(pins.at(i,1));
        check(expectedOwner[n]==net,"candidate pin ownership missing");if(!core.data[n])usedNoncore[n]=1;}
    for(size_t i=0;i<fp.count;++i){auto net=fp.at(i,0);check(net<nets.count,"PIP net bounds");if(nets.at(net,0)!=0)continue;++candidatePips;auto dir=fp.at(i,7)&1;
        auto src=mapped(fp.at(i,dir?2:1)),dst=mapped(fp.at(i,dir?1:2)),pid=pm.at(i,0);check(pid<pipMask.count&&pid<(1u<<31),"PIP key bounds");
        if(!core.data[src]||!core.data[dst]){
            check(originalAccess.emplace((pid<<1)|dir,Access{net,src,dst}).second,"duplicate original access key");
            for(auto n:{src,dst})if(!core.data[n]){claim(n,net);usedNoncore[n]=1;}
            if(core.data[src]&&!core.data[dst])claim(src,net);
        }
    }
    size_t sdkMatched=0,sdkRootsMatched=0,singleSlrUbump=0,privateCount=0,newProjected=0,blockedNoncore=0,blockedPinfeed=0,blocked=0,exclusive=0;
    for(size_t n=0;n<nodes.count;++n){check(le32(owner.data+4*n)==expectedOwner[n],"exclusive owner differs from original pins/access");
        auto expectedPrivate=usedNoncore[n]?expectedOwner[n]:none;check(le32(privateOwner.data+4*n)==expectedPrivate,"private noncore owner differs from original footprint");
        privateCount+=usedNoncore[n]!=0;newProjected+=core.data[n]&&le32(baseOwner.data+4*n)==none&&expectedOwner[n]!=none;
        bool sdkInput=nodes.at(n,7)==6&&sdkKeys.count((uint64_t(nodes.at(n,3))<<32)|nodes.at(n,4));sdkMatched+=sdkInput;
        if(nodes.at(n,7)==19){check(sdkRootKeys.count((uint64_t(nodes.at(n,3))<<32)|nodes.at(n,4)),"Laguna data intent not present in SDK UBUMPs");++sdkRootsMatched;singleSlrUbump+=(nodes.at(n,5)&(nodes.at(n,5)-1))==0;}
        check(laguna.data[n]==sdkInput,"Laguna input differs from SDK topology");
        auto bits=baseMask.data[n];if(!core.data[n]&&!usedNoncore[n]){bits|=32;++blockedNoncore;}
        if(core.data[n]&&nodes.at(n,7)==6&&expectedOwner[n]==none&&!sdkInput){bits|=64;++blockedPinfeed;}
        check(mask.data[n]==bits,"qualified node mask differs");expectedMask[n]=bits;blocked+=bits!=0;exclusive+=expectedOwner[n]!=none;
    }
    check(sdkMatched==sdk.count,"SDK Laguna input absent from native graph");
    check(sdkRootsMatched==sdkUbump.count,"SDK UBUMP absent from Laguna data intents");
    size_t keptCore=0,keptAccess=0,foreign=0;uint64_t position=0;
    for(size_t src=0;src<nodes.count;++src){check(fo.offset(src)==position,"filtered offset/start mismatch");auto begin=ro.offset(src),end=ro.offset(src+1);
        check(begin<=end&&end<=ra.count,"raw CSR range");
        for(auto i=begin;i<end;++i){auto dst=ra.dst(i),key=ra.edge(i);check(dst<nodes.count&&(key>>1)<pipMask.count,"raw arc bounds");
            if(expectedMask[src]||expectedMask[dst]||pipMask.data[key>>1])continue;
            if(expectedOwner[src]!=none&&expectedOwner[dst]!=none&&expectedOwner[src]!=expectedOwner[dst]){++foreign;continue;}
            bool bothCore=core.data[src]&&core.data[dst];
            if(!bothCore){auto found=originalAccess.find(key);if(found==originalAccess.end())continue;
                check(found->second.src==src&&found->second.dst==dst,"access PIP native endpoints differ");}
            check(position<fa.count&&fa.dst(position)==dst&&fa.edge(position)==key,"missing/extra/reordered permitted PIP");
            ++position;if(bothCore)++keptCore;else ++keptAccess;
        }
        check(fo.offset(src+1)==position,"filtered offset/end mismatch");
        if(src%20000000==0)std::cout<<"verified_search_nodes="<<src<<std::endl;
    }
    check(position==fa.count&&keptAccess==originalAccess.size(),"permitted arc coverage");
    for(size_t i=0;i<fp.count;++i){auto net=fp.at(i,0);if(nets.at(net,0)!=0)continue;auto dir=fp.at(i,7)&1,src=mapped(fp.at(i,dir?2:1)),dst=mapped(fp.at(i,dir?1:2)),key=(pm.at(i,0)<<1)|dir;
        auto lo=fo.offset(src),end=fo.offset(src+1),hi=end;auto wanted=std::make_pair(dst,key);
        while(lo<hi){auto mid=lo+(hi-lo)/2;if(std::make_pair(fa.dst(mid),fa.edge(mid))<wanted)lo=mid+1;else hi=mid;}
        check(lo<end&&std::make_pair(fa.dst(lo),fa.edge(lo))==wanted&&(expectedOwner[src]==none||expectedOwner[src]==net)&&(expectedOwner[dst]==none||expectedOwner[dst]==net),"original candidate PIP missing/forbidden");
    }
    std::ofstream report(out/"audit.json");report<<"{\n  \"schema\":\"dieroute.native_search_graph_audit.v1\",\n  \"passed\":true,\n  \"nodes\":"<<nodes.count<<",\n  \"raw_arcs\":"<<ra.count<<",\n  \"search_arcs\":"<<fa.count
        <<",\n  \"core_core_arcs\":"<<keptCore<<",\n  \"fixed_access_arcs\":"<<keptAccess<<",\n  \"private_noncore_nodes\":"<<privateCount<<",\n  \"new_projected_sink_nodes\":"<<newProjected
        <<",\n  \"laguna_pinfeed_nodes\":"<<sdkMatched<<",\n  \"unused_pinfeed_nodes_blocked\":"<<blockedPinfeed<<",\n  \"unused_noncore_nodes_blocked\":"<<blockedNoncore
        <<",\n  \"SDK_ubump_nodes\":"<<sdkRootsMatched<<",\n  \"single_slr_ubump_nodes\":"<<singleSlrUbump
        <<",\n  \"all_blocked_nodes\":"<<blocked<<",\n  \"exclusive_net_nodes\":"<<exclusive<<",\n  \"foreign_terminal_owner_arcs_removed\":"<<foreign<<",\n  \"candidate_pips_checked\":"<<candidatePips
        <<",\n  \"scope\":\"all qualified entries checked against original candidates and raw graph, with independent SDK Laguna topology; no new routing or timing/QoR claim\"\n}\n";
    report.close();check(bool(report),"audit output failed");std::cout<<"verified_search_arcs="<<fa.count<<" SDK_laguna_inputs="<<sdkMatched<<std::endl;return 0;
}catch(const std::exception& e){std::cerr<<"search graph verification failed: "<<e.what()<<std::endl;return 1;}}
