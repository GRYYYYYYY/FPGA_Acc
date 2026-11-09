#include "native_csr_io.hpp"
#include <algorithm>
#include <iostream>
#include <unordered_map>
#include <vector>
using namespace dieroute::native;
// Exact quotient of qualified adjacency by (native representative tile,intent).
// Relax net ownership and intra-group connectivity ONLY for the lower bound.
int main(int argc,char** argv){try{
    check(argc==5,"usage: build_native_quotient GRAPH SEARCH ARCH NEW_OUTPUT");
    fs::path graph=argv[1],search=argv[2],out=argv[4];auto arch=fingerprint(argv[3]);check(fs::create_directory(out),"new output required");
    Raw nodes(graph/"nodes.bin",16);Container offsets(search/"offsets.bin",offsets_type,8,arch),arcs(search/"arcs.bin",arcs_type,8,arch),mask(search/"node_protection.bin",0x4452000a,1,arch);
    check(nodes.count<none&&mask.count==nodes.count&&offsets.count==nodes.count+1,"node coverage");check(offsets.offset(0)==0&&offsets.offset(nodes.count)==arcs.count,"CSR coverage");
    std::unordered_map<uint64_t,uint32_t> groups;std::vector<uint64_t> keys;std::vector<uint32_t> ids(nodes.count,none);
    for(size_t n=0;n<nodes.count;++n)if(!mask.data[n]){
        uint64_t key=(uint64_t(nodes.at(n,3))<<32)|nodes.at(n,7);auto found=groups.find(key);
        if(found==groups.end()){check(keys.size()<none,"group ID width");auto id=uint32_t(keys.size());groups.emplace(key,id);keys.push_back(key);ids[n]=id;}else ids[n]=found->second;
    }
    std::vector<uint64_t> reverse;reverse.reserve(arcs.count);size_t intra=0;
    for(size_t n=0;n<nodes.count;++n){auto begin=offsets.offset(n),end=offsets.offset(n+1);check(begin<=end&&end<=arcs.count,"CSR row bounds");
        for(auto i=begin;i<end;++i){auto to=arcs.dst(i);check(to<nodes.count&&ids[n]!=none&&ids[to]!=none,"protected or invalid adjacency");
            if(ids[n]==ids[to])++intra;else reverse.push_back((uint64_t(ids[to])<<32)|ids[n]);}
    }
    std::cout<<"groups="<<keys.size()<<" raw_inter_group_arcs="<<reverse.size()<<std::endl;
    std::sort(reverse.begin(),reverse.end());reverse.erase(std::unique(reverse.begin(),reverse.end()),reverse.end());
    std::vector<uint64_t> off(keys.size()+1);
    for(auto edge:reverse)++off[(edge>>32)+1];
    for(size_t i=1;i<off.size();++i)off[i]+=off[i-1];
    auto write=[&](const char* name,uint32_t type,const auto& v,size_t width,auto value){Writer w(out/name,type,v.size(),arch);std::vector<unsigned char> bytes(1<<20);
        for(size_t start=0;start<v.size();){auto count=std::min(bytes.size()/width,v.size()-start);for(size_t i=0;i<count;++i)value(bytes.data()+i*width,v[start+i]);w.append(bytes.data(),count*width);start+=count;}w.finish(width);};
    write("node_groups.bin",0x4452000d,ids,4,[](auto* p,auto v){put32(p,v);});
    write("reverse_offsets.bin",0x4452000e,off,8,[](auto* p,auto v){put64(p,v);});
    write("reverse_sources.bin",0x4452000f,reverse,4,[](auto* p,auto v){put32(p,uint32_t(v));});
    write("groups.bin",0x44520010,keys,8,[](auto* p,auto v){put32(p,v>>32);put32(p+4,uint32_t(v));});
    std::ofstream audit(out/"audit.json");audit<<"{\"schema\":\"dieroute.native_quotient.v1\",\"nodes\":"<<nodes.count<<",\"native_arcs\":"<<arcs.count<<",\"groups\":"<<keys.size()<<",\"quotient_arcs\":"<<reverse.size()<<",\"intra_group_native_arcs\":"<<intra<<",\"scope\":\"exact tile/intent quotient for hop lower bounds; net ownership and intra-group connectivity relaxed; not a routing graph or physical delay model\"}\n";
    audit.close();check(bool(audit),"audit write failure");std::cout<<"quotient_arcs="<<reverse.size()<<std::endl;return 0;
}catch(const std::exception& e){std::cerr<<"quotient build failed: "<<e.what()<<std::endl;return 1;}}
