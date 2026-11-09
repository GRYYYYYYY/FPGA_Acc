#include "native_csr_io.hpp"
#include <iostream>
#include <unordered_set>
#include <vector>
using namespace dieroute::native;
int main(int argc,char** argv){try{
    check(argc==6,"usage: verify_native_quotient GRAPH SEARCH QUOTIENT ARCH NEW_OUTPUT");
    fs::path graph=argv[1],search=argv[2],q=argv[3],out=argv[5];auto arch=fingerprint(argv[4]);check(fs::create_directory(out),"new output required");
    Raw nodes(graph/"nodes.bin",16);Container no(search/"offsets.bin",offsets_type,8,arch),na(search/"arcs.bin",arcs_type,8,arch),mask(search/"node_protection.bin",0x4452000a,1,arch),
        ids(q/"node_groups.bin",0x4452000d,4,arch),off(q/"reverse_offsets.bin",0x4452000e,8,arch),src(q/"reverse_sources.bin",0x4452000f,4,arch),groups(q/"groups.bin",0x44520010,8,arch);
    check(ids.count==nodes.count&&mask.count==nodes.count&&no.count==nodes.count+1&&off.count==groups.count+1,"quotient/native coverage");
    check(no.offset(0)==0&&no.offset(nodes.count)==na.count&&le64(off.data)==0&&le64(off.data+groups.count*8)==src.count,"offset coverage");
    std::unordered_set<uint64_t> keys;std::vector<bool> used(groups.count),seen(src.count);
    for(size_t g=0;g<groups.count;++g){check(keys.insert(le64(groups.data+8*g)).second,"duplicate group descriptor");auto begin=le64(off.data+8*g),end=le64(off.data+8*(g+1));check(begin<=end&&end<=src.count,"quotient row bounds");
        uint32_t previous=0;for(auto i=begin;i<end;++i){auto from=le32(src.data+4*i);check(from<groups.count&&from!=g&&(i==begin||from>previous),"quotient source ordering/range/self-loop");previous=from;}}
    for(size_t n=0;n<nodes.count;++n){auto g=le32(ids.data+4*n);if(mask.data[n]){check(g==none,"protected node has group");continue;}
        check(g<groups.count,"missing node group");check(le32(groups.data+8*g)==nodes.at(n,3)&&le32(groups.data+8*g+4)==nodes.at(n,7),"node group descriptor mismatch");used[g]=true;}
    for(auto yes:used)check(yes,"empty invented group");
    size_t intra=0;
    for(size_t n=0;n<nodes.count;++n){auto begin=no.offset(n),end=no.offset(n+1);check(begin<=end&&end<=na.count,"native row bounds");auto from=le32(ids.data+4*n);
        for(auto i=begin;i<end;++i){auto dst=na.dst(i);check(dst<nodes.count,"native destination bounds");auto to=le32(ids.data+4*dst);check(from<groups.count&&to<groups.count,"native arc touches protected node");if(from==to){++intra;continue;}
            auto lo=le64(off.data+8*to),stop=le64(off.data+8*(to+1)),hi=stop;
            while(lo<hi){auto mid=lo+(hi-lo)/2;if(le32(src.data+4*mid)<from)lo=mid+1;else hi=mid;}
            check(lo<stop&&le32(src.data+4*lo)==from,"native edge missing from quotient");seen[lo]=true;}
    }
    for(auto yes:seen)check(yes,"invented quotient edge");
    std::ofstream report(out/"audit.json");report<<"{\"schema\":\"dieroute.native_quotient_audit.v1\",\"passed\":true,\"nodes\":"<<nodes.count<<",\"native_arcs\":"<<na.count<<",\"groups\":"<<groups.count<<",\"quotient_arcs\":"<<src.count<<",\"intra_group_native_arcs\":"<<intra<<",\"scope\":\"exact directed quotient checked against every native node/edge; reverse hop distances are consistent lower bounds, not calibrated delays\"}\n";
    report.close();check(bool(report),"audit output failure");std::cout<<"verified_quotient_groups="<<groups.count<<" edges="<<src.count<<std::endl;return 0;
}catch(const std::exception& e){std::cerr<<"quotient verification failed: "<<e.what()<<std::endl;return 1;}}
