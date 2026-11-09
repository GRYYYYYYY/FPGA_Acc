#pragma once
#include "../hbm_abi/snapshot_abi.hpp"
namespace tileplace_wire_commit {
// Input transaction13 and selected indices from conflict selection. Block8 IDs
// are unique/canonical (host validated), position2 and trial3 preserve all bits.
// Validate the whole selected batch before mutating positions.
// Status 1 record/range, 2 unknown/wide ID, 3 repeated block, 4 scaling.
inline std::uint64_t find(const std::uint64_t* blocks,std::uint64_t count,std::uint32_t id){
 std::uint64_t lo=0,hi=count;while(lo<hi){auto mid=lo+(hi-lo)/2;auto value=std::uint32_t(blocks[8*mid]);if(value<id)lo=mid+1;else hi=mid;}
 return lo<count&&std::uint32_t(blocks[8*lo])==id?lo:count;
}
inline std::uint64_t commit(const std::uint64_t* records,std::uint32_t count,
 const std::uint32_t* selected,std::uint32_t selected_count,
 const std::uint64_t* trials,std::uint64_t trial_count,
 const std::uint64_t* blocks,std::uint64_t block_count,std::uint64_t* positions,unsigned& status){
 status=0;if(block_count>UINT64_MAX/8||trial_count>UINT64_MAX/3){status=4;return 0;}
 std::uint64_t moved=0;
 for(std::uint32_t i=0;i<selected_count;++i){
  if(selected[i]>=count){status=1;return 0;}
  auto r=records+13ULL*selected[i];tileplace_hbm::Range range{r[5],r[6]};
  if(!tileplace_hbm::valid_range(range,trial_count)){status=1;return 0;}
  for(std::uint64_t j=0;j<range.count;++j){auto t=trials+3*(range.offset+j);
   if(t[0]>UINT32_MAX||find(blocks,block_count,std::uint32_t(t[0]))==block_count){status=2;return 0;}
   for(std::uint32_t a=0;a<=i;++a){auto old=records+13ULL*selected[a];auto end=a==i?j:old[6];
    for(std::uint64_t b=0;b<end;++b)if(trials[3*(old[5]+b)]==t[0]){status=3;return 0;}
   }
  }
  // Unique known IDs bound this total by block_count.
  moved+=range.count;
 }
 for(std::uint32_t i=0;i<selected_count;++i){auto r=records+13ULL*selected[i];
  for(std::uint64_t j=0;j<r[6];++j){auto t=trials+3*(r[5]+j);auto b=find(blocks,block_count,std::uint32_t(t[0]));positions[2*b]=t[1];positions[2*b+1]=t[2];}
 }
 return moved;
}
}
