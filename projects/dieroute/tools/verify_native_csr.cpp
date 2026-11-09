#include "native_csr_io.hpp"
#include <algorithm>
#include <iostream>
#include <tuple>
#include <vector>
using namespace dieroute::native;
int main(int argc,char** argv){
    try {
        check(argc==7,"usage: verify_native_csr GRAPH_DIR MAPPED_OCCUPANCY_DIR FOOTPRINT_DIR CSR_DIR ARCH_FINGERPRINT NEW_OUTPUT_DIR");
        fs::path graph=argv[1],mapped=argv[2],footprint=argv[3],csr=argv[4],out=argv[6];auto arch=fingerprint(argv[5]);
        check(fs::create_directory(out),"output must be new");
        Raw nodes(graph/"nodes.bin",16),pips(graph/"pips.bin",8),occupied(mapped/"occupied_nodes.bin",8);
        Container offsets(csr/"offsets.bin",offsets_type,8,arch),arcs(csr/"arcs.bin",arcs_type,8,arch),protection(csr/"protection.bin",protection_type,1,arch);
        check(offsets.count==nodes.count+1 && protection.count==nodes.count,"CSR node coverage");
        check(offsets.offset(0)==0 && offsets.offset(nodes.count)==arcs.count,"CSR boundary offsets");
        std::vector<unsigned char> directions(pips.count,0),expectedProtection(nodes.count,0),seenOccupation(nodes.count,0);
        size_t nonempty=0,maxDegree=0,parallelGroups=0,parallelExtra=0,selfArcs=0;
        std::ofstream parallel(out/"parallel_pip_examples.csv");parallel<<"source_node,destination_node,first_edge_key,second_edge_key\n";size_t examples=0;
        for(size_t n=0;n<nodes.count;n++){
            uint64_t begin=offsets.offset(n),end=offsets.offset(n+1);check(begin<=end && end<=arcs.count,"CSR offset monotonicity");
            nonempty+=end>begin;maxDegree=std::max(maxDegree,size_t(end-begin));uint32_t prevDst=none,prevKey=none;size_t group=0;
            for(size_t i=begin;i<end;i++){
                uint32_t dst=arcs.dst(i),key=arcs.edge(i),pid=key>>1,dir=key&1;
                check(dst<nodes.count && pid<pips.count,"arc destination/PIP bounds");
                check(i==begin || std::make_pair(dst,key)>std::make_pair(prevDst,prevKey),"arc order or duplicate");
                uint32_t a=pips.at(pid,1),b=pips.at(pid,2),f=pips.at(pid,7),slr=pips.at(pid,6);
                check(a!=none && b!=none,"CSR includes missing-endpoint PIP");
                check((f&2) || dir==(f&1),"illegal PIP direction");
                check(n==(dir?b:a) && dst==(dir?a:b),"arc endpoint/PIP identity");
                check(slr<8 && (nodes.at(n,5)&(1u<<slr)) && (nodes.at(dst,5)&(1u<<slr)),"arc SLR membership");
                check(!(directions[pid]&(1u<<dir)),"duplicate PIP direction");directions[pid]|=1u<<dir;
                if(dst==prevDst){parallelExtra++;if(group==1){parallelGroups++;if(examples++<64)parallel<<n<<','<<dst<<','<<prevKey<<','<<key<<'\n';}group++;}else group=1;
                prevDst=dst;prevKey=key;selfArcs+=n==dst;
            }
            uint32_t f=nodes.at(n,8);if(f&3)expectedProtection[n]|=4;if(f&4)expectedProtection[n]|=8;
            if(n%20000000==0)std::cout<<"verified_CSR_nodes="<<n<<std::endl;
        }
        size_t missing=0;
        for(size_t i=0;i<pips.count;i++){
            uint32_t a=pips.at(i,1),b=pips.at(i,2),f=pips.at(i,7);uint8_t expected=0;
            if(a==none || b==none)missing++;else expected=(f&2)?3:uint8_t(1u<<(f&1));
            check(directions[i]==expected,"PIP orientation coverage");
        }
        for(size_t i=0;i<occupied.count;i++){
            uint32_t n=occupied.at(i,0);check(n<nodes.count && !seenOccupation[n],"mapped occupancy duplicate/range");seenOccupation[n]=1;
            if(occupied.at(i,4))expectedProtection[n]|=1;
            if(occupied.at(i,6)&4)expectedProtection[n]|=2;
        }
        std::array<uint64_t,16> masks{};
        for(size_t n=0;n<nodes.count;n++){check(protection.data[n]==expectedProtection[n],"immutable resource metadata mismatch");masks[protection.data[n]]++;}
        Raw fp(footprint/"pips.bin",8),pm(mapped/"footprint_pip_map.bin",1),nm(mapped/"footprint_node_map.bin",1);
        check(fp.count==pm.count,"DCP PIP map coverage");
        size_t reversedUsed=0;
        for(size_t i=0;i<fp.count;i++){
            uint32_t pid=pm.at(i,0),dir=fp.at(i,7)&1,key=uint32_t((uint64_t(pid)<<1)|dir);
            check(pid<pips.count,"DCP PIP catalog bounds");uint32_t source=nm.at(fp.at(i,dir?2:1),0),sink=nm.at(fp.at(i,dir?1:2),0);reversedUsed+=dir;
            size_t lo=offsets.offset(source),end=offsets.offset(source+1),hi=end;auto wanted=std::make_pair(sink,key);
            while(lo<hi){size_t mid=lo+(hi-lo)/2;if(std::make_pair(arcs.dst(mid),arcs.edge(mid))<wanted)lo=mid+1;else hi=mid;}
            check(lo<end && std::make_pair(arcs.dst(lo),arcs.edge(lo))==wanted,"original DCP PIP orientation absent from CSR");
        }
        std::ofstream report(out/"audit.json");report<<"{\n  \"schema\": \"dieroute.native_csr_audit.v1\",\n  \"structural_checks_passed\": true,\n"
            <<"  \"nodes\": "<<nodes.count<<",\n  \"pips\": "<<pips.count<<",\n  \"arcs\": "<<arcs.count
            <<",\n  \"missing_endpoint_pips\": "<<missing<<",\n  \"nodes_with_outgoing_arcs\": "<<nonempty<<",\n  \"max_outdegree\": "<<maxDegree
            <<",\n  \"parallel_destination_groups\": "<<parallelGroups<<",\n  \"parallel_extra_arcs\": "<<parallelExtra<<",\n  \"self_arcs\": "<<selfArcs
            <<",\n  \"original_DCP_PIPs_direction_matched\": "<<fp.count<<",\n  \"original_reversed_PIPs\": "<<reversedUsed<<",\n  \"protection_masks\": {";
        bool comma=false;for(size_t m=0;m<masks.size();m++)if(masks[m]){if(comma)report<<',';comma=true;report<<'"'<<m<<"\":"<<masks[m];}
        report<<"},\n  \"scope\": \"all PIP orientations and original DCP directions preserved; resource masks are metadata, not implemented controller protection\"\n}\n";
        std::cout<<"verified_arcs="<<arcs.count<<" original_pips="<<fp.count<<std::endl;return 0;
    }catch(const std::exception& e){std::cerr<<"verification failed: "<<e.what()<<std::endl;return 1;}
}
