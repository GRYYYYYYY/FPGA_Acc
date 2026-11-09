#pragma once
#include "native_csr_io.hpp"
#include <algorithm>
#include <vector>
namespace dieroute::native {
class QuotientPotential {
    Container ids_,offsets_,sources_,groups_;
    std::vector<uint32_t> distances_,queue_;
    uint32_t ceiling_=none;
public:
    uint64_t expanded=0,edge_visits=0;
    QuotientPotential(const fs::path& dir,const Fingerprint& arch,uint64_t nodes)
        :ids_(dir/"node_groups.bin",0x4452000d,4,arch),offsets_(dir/"reverse_offsets.bin",0x4452000e,8,arch),
         sources_(dir/"reverse_sources.bin",0x4452000f,4,arch),groups_(dir/"groups.bin",0x44520010,8,arch){
        check(ids_.count==nodes&&groups_.count<none&&offsets_.count==groups_.count+1,"quotient coverage");
        check(le64(offsets_.data)==0&&le64(offsets_.data+groups_.count*8)==sources_.count,"quotient offsets coverage");
    }
    void prepare(uint32_t sink,uint32_t source=none,uint64_t cost_ceiling=UINT64_MAX){
        check(sink<ids_.count,"quotient sink bounds");auto group=le32(ids_.data+sink*4);check(group<groups_.count,"quotient sink group");
        auto sourceGroup=none;if(source!=none){check(source<ids_.count,"quotient source bounds");sourceGroup=le32(ids_.data+source*4);check(sourceGroup<groups_.count,"quotient source group");}
        distances_.assign(groups_.count,none);queue_.clear();expanded=edge_visits=0;ceiling_=none;
        // For a search capped at C, exact distances above C cannot participate.
        // Finish layers < C+1, then clamp everything else to C+1. This is still
        // consistent and leaves every admitted (g+h <= C) label unchanged.
        const auto horizon=cost_ceiling<uint64_t(none)-1?uint32_t(cost_ceiling+1):none;
        ceiling_=horizon;
        distances_[group]=0;queue_.push_back(group);
        for(size_t pos=0;pos<queue_.size();++pos){auto n=queue_[pos];
            // FIFO layers ensure every distance < source distance is complete.
            // min(exact_distance,ceiling) is consistent, including undiscovered
            // or unreachable groups, whose clamped value is the ceiling.
            if(n==sourceGroup||distances_[n]>=horizon){ceiling_=distances_[n];break;}
            ++expanded;auto begin=le64(offsets_.data+n*8),end=le64(offsets_.data+(n+1)*8);
            check(begin<=end&&end<=sources_.count,"quotient row bounds");
            for(auto edge=begin;edge<end;++edge){auto from=le32(sources_.data+edge*4);check(from<groups_.count,"quotient predecessor bounds");++edge_visits;
                if(distances_[from]==none){check(distances_[n]<none-1,"quotient distance overflow");distances_[from]=distances_[n]+1;queue_.push_back(from);}}
        }
    }
    uint64_t operator()(uint32_t node)const{
        check(node<ids_.count,"quotient node bounds");auto g=le32(ids_.data+node*4);check(g==none||g<distances_.size(),"quotient group bounds/unprepared");
        if(g==none)return UINT64_MAX;
        auto distance=std::min(distances_[g],ceiling_);return distance==none?UINT64_MAX:distance;
    }
    size_t retained_bytes()const{return distances_.capacity()*4+queue_.capacity()*4;}
};
} // namespace dieroute::native
