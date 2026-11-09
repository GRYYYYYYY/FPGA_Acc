#include "native_quotient.hpp"
#include <iostream>
using namespace dieroute::native;
int main(int argc,char** argv){try{
    check(argc==3,"usage: quotient_potential_tb QUOTIENT ARCH");fs::path dir=argv[1];auto arch=fingerprint(argv[2]);
    Container ids(dir/"node_groups.bin",0x4452000d,4,arch),off(dir/"reverse_offsets.bin",0x4452000e,8,arch),edges(dir/"reverse_sources.bin",0x4452000f,4,arch);
    check(ids.count<1000,"fixture must be small");std::vector<uint32_t> representative(off.count-1,none);
    for(uint32_t n=0;n<ids.count;++n){auto g=le32(ids.data+4*n);if(g!=none){check(g<representative.size(),"fixture group bounds");representative[g]=n;}}
    QuotientPotential full(dir,arch,ids.count),bounded(dir,arch,ids.count);size_t queries=0;
    for(uint32_t sink=0;sink<ids.count;++sink)if(le32(ids.data+4*sink)!=none){full.prepare(sink);
        for(uint32_t source=0;source<ids.count;++source)if(le32(ids.data+4*source)!=none)for(auto cost_ceiling:std::vector<uint64_t>{UINT64_MAX,0,1,2,5,UINT32_MAX}){bounded.prepare(sink,source,cost_ceiling);auto ceiling=std::min(full(source),cost_ceiling<UINT32_MAX-1?cost_ceiling+1:UINT64_MAX);++queries;
            for(uint32_t n=0;n<ids.count;++n){auto expected=le32(ids.data+4*n)==none?UINT64_MAX:std::min(full(n),ceiling);check(bounded(n)==expected,"source/cost radius is not exactly clamped full distance");}
            check(bounded(sink)==0,"sink potential");
            for(size_t to=0;to<representative.size();++to)for(auto edge=le64(off.data+8*to);edge<le64(off.data+8*(to+1));++edge){auto from=le32(edges.data+4*edge);auto a=bounded(representative[from]),b=bounded(representative[to]);
                if(b!=UINT64_MAX)check(a!=UINT64_MAX&&a<=b+1,"inconsistent quotient potential");}
        }
    }
    std::cout<<"clamped distances and edge consistency verified for "<<queries<<" source/sink pairs\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
