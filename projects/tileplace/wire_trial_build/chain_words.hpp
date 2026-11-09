#pragma once
#include "../wire_candidates/translation_words.hpp"
namespace tileplace_wire_trial_build {
// Two/three singleton chain: first->target, second->next, optional third->first's old location.
// Caller has checked fixed units/occupancy. All IDs must be distinct existing blocks.
// Status 1 chain size, 2 capacity, 3 unknown ID, 4 duplicate ID, 5 scaling. Atomic output.
inline std::uint32_t chain(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,const std::uint32_t* ids,std::uint32_t count,const std::uint64_t* target,const std::uint64_t* next,std::uint64_t* output,std::uint32_t capacity,std::uint32_t& status){
 status=0;if(count!=2&&count!=3){status=1;return 0;}if(count>capacity){status=2;return 0;}if(bc>UINT64_MAX/8){status=5;return 0;}
 std::uint64_t indices[3]{};for(unsigned i=0;i<count;++i){indices[i]=tileplace_wire_candidates::block_index(blocks,bc,ids[i]);if(indices[i]==bc){status=3;return 0;}for(unsigned j=0;j<i;++j)if(ids[i]==ids[j]){status=4;return 0;}}
 unsigned order[3]={0,1,2};for(unsigned i=1;i<count;++i){unsigned j=i;while(j&&ids[order[j]]<ids[order[j-1]]){auto t=order[j];order[j]=order[j-1];order[j-1]=t;--j;}}
 for(unsigned j=0;j<count;++j){auto i=order[j];const auto* p=i==0?target:i==1?next:positions+2*indices[0];output[3*j]=ids[i];output[3*j+1]=p[0];output[3*j+2]=p[1];}return count;
}
}
