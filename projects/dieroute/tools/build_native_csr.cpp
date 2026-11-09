#include "native_csr_io.hpp"
#include <algorithm>
#include <iostream>
#include <vector>
using namespace dieroute::native;
int main(int argc,char** argv){
    try {
        check(argc==5,"usage: build_native_csr GRAPH_DIR MAPPED_OCCUPANCY_DIR ARCH_FINGERPRINT NEW_OUTPUT_DIR");
        fs::path graph=argv[1],mapped=argv[2],out=argv[4];check(fs::create_directory(out),"output must be new");auto arch=fingerprint(argv[3]);
        Raw nodes(graph/"nodes.bin",16),pips(graph/"pips.bin",8),occupied(mapped/"occupied_nodes.bin",8);
        check(nodes.count<none && pips.count<=uint64_t(1)<<31,"packed edge reference width exceeded");
        std::vector<uint64_t> offsets(nodes.count+1,0);size_t rejected=0;
        std::ofstream exclusions(out/"missing_endpoint_pips.csv");exclusions<<"pip_id,start_node,end_node,flags\n";
        auto visit=[&](size_t id,auto callback){
            uint32_t a=pips.at(id,1),b=pips.at(id,2),flags=pips.at(id,7);
            check(pips.at(id,0)==id && !(flags&~255u),"PIP ID/flags");
            check((a==none || a<nodes.count) && (b==none || b<nodes.count),"PIP endpoint out of range");
            if(a==none || b==none)return false;
            check(a<nodes.count && b<nodes.count,"PIP endpoint out of range");
            if(flags&2){callback(a,b,uint32_t(id<<1));callback(b,a,uint32_t((id<<1)|1));}
            else if(flags&1)callback(b,a,uint32_t((id<<1)|1));else callback(a,b,uint32_t(id<<1));
            return true;
        };
        for(size_t i=0;i<pips.count;i++)if(!visit(i,[&](uint32_t a,uint32_t,uint32_t){offsets[a+1]++;})){
            rejected++;exclusions<<i<<','<<pips.at(i,1)<<','<<pips.at(i,2)<<','<<pips.at(i,7)<<'\n';
        }
        for(size_t n=1;n<offsets.size();n++){check(offsets[n]<=UINT64_MAX-offsets[n-1],"CSR offset overflow");offsets[n]+=offsets[n-1];}
        check(offsets.back()<=SIZE_MAX/sizeof(Arc),"arc allocation width");std::vector<Arc> arcs(offsets.back());auto cursor=offsets;
        for(size_t i=0;i<pips.count;i++)visit(i,[&](uint32_t a,uint32_t b,uint32_t key){arcs[cursor[a]++]={b,key};});
        std::cout<<"assembled_arcs="<<arcs.size()<<std::endl;
        size_t nonempty=0,maxDegree=0,parallelGroups=0,parallelExtra=0,selfArcs=0;
        for(size_t n=0;n<nodes.count;n++){
            check(cursor[n]==offsets[n+1],"CSR fill mismatch");auto begin=arcs.begin()+offsets[n],end=arcs.begin()+offsets[n+1];
            std::sort(begin,end,[](const Arc& a,const Arc& b){return a.dst<b.dst || (a.dst==b.dst && a.edge<b.edge);});
            size_t degree=offsets[n+1]-offsets[n];nonempty+=degree>0;maxDegree=std::max(maxDegree,degree);
            uint32_t previous=none;size_t group=0;
            for(auto it=begin;it!=end;++it){selfArcs+=it->dst==n;
                if(it->dst==previous){parallelExtra++;if(group==1)parallelGroups++;group++;}else{previous=it->dst;group=1;}
            }
        }
        cursor.clear();cursor.shrink_to_fit();
        std::vector<unsigned char> protection(nodes.count,0),used(nodes.count,0);
        for(size_t n=0;n<nodes.count;n++){auto f=nodes.at(n,8);if(f&3)protection[n]|=4;if(f&4)protection[n]|=8;}
        for(size_t i=0;i<occupied.count;i++){
            uint32_t n=occupied.at(i,0);check(n<nodes.count && !used[n],"mapped occupancy duplicate/range");used[n]=1;
            check(uint64_t(occupied.at(i,4))+occupied.at(i,5)==occupied.at(i,3),"mapped owner counts");
            if(occupied.at(i,4))protection[n]|=1;
            if(occupied.at(i,6)&4)protection[n]|=2;
        }
        std::array<uint64_t,16> masks{};for(auto m:protection)masks[m]++;
        Writer offsetOut(out/"offsets.bin",offsets_type,offsets.size(),arch),arcOut(out/"arcs.bin",arcs_type,arcs.size(),arch),protectOut(out/"protection.bin",protection_type,protection.size(),arch);
        std::vector<unsigned char> block(1<<20);
        for(size_t begin=0;begin<offsets.size();){size_t len=std::min(block.size()/8,offsets.size()-begin);for(size_t j=0;j<len;j++)put64(block.data()+8*j,offsets[begin+j]);offsetOut.append(block.data(),len*8);begin+=len;}
        offsetOut.finish(8);
        for(size_t begin=0;begin<arcs.size();){size_t len=std::min(block.size()/8,arcs.size()-begin);for(size_t j=0;j<len;j++){put32(block.data()+8*j,arcs[begin+j].dst);put32(block.data()+8*j+4,arcs[begin+j].edge);}arcOut.append(block.data(),len*8);begin+=len;}
        arcOut.finish(8);protectOut.append(protection.data(),protection.size());protectOut.finish(1);
        std::ofstream report(out/"summary.json");report<<"{\n  \"schema\": \"dieroute.native_csr.v1\",\n  \"nodes\": "<<nodes.count<<",\n  \"pips\": "<<pips.count
            <<",\n  \"arcs\": "<<arcs.size()<<",\n  \"missing_endpoint_pips\": "<<rejected<<",\n  \"nodes_with_outgoing_arcs\": "<<nonempty
            <<",\n  \"max_outdegree\": "<<maxDegree<<",\n  \"parallel_destination_groups\": "<<parallelGroups<<",\n  \"parallel_extra_arcs\": "<<parallelExtra
            <<",\n  \"self_arcs\": "<<selfArcs<<",\n  \"protection_masks\": {";
        bool comma=false;for(size_t m=0;m<masks.size();m++)if(masks[m]){if(comma)report<<',';comma=true;report<<'"'<<m<<"\":"<<masks[m];}
        report<<"},\n  \"scope\": \"raw directed adjacency with PIP identity and immutable-resource metadata; no design-eligible routing, capacity or delay claim\"\n}\n";
        std::cout<<"built_nodes="<<nodes.count<<" arcs="<<arcs.size()<<" parallel_groups="<<parallelGroups<<std::endl;return 0;
    }catch(const std::exception& e){std::cerr<<"build failed: "<<e.what()<<std::endl;return 1;}
}
