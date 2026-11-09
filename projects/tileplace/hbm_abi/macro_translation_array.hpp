#pragma once
#include "trial_legality_array.hpp"
namespace tileplace_hbm {
inline std::uint64_t translation_index(const Block* blocks,std::uint64_t count,std::uint32_t id){
 std::uint64_t low=0,high=count;
 while(low<high){auto mid=low+(high-low)/2;if(blocks[mid].id<id)low=mid+1;else high=mid;}
 return low<count&&blocks[low].id==id?low:count;
}
inline bool translated_location(Location p,Location target,Location root,Location& out){
 std::int64_t values[4]={std::int64_t(p.x)+target.x-root.x,std::int64_t(p.y)+target.y-root.y,
  std::int64_t(p.subtile)+target.subtile-root.subtile,std::int64_t(p.layer)+target.layer-root.layer};
 for(unsigned i=0;i<4;++i)if(values[i]<INT32_MIN||values[i]>INT32_MAX)return false;
 out={std::int32_t(values[0]),std::int32_t(values[1]),std::int32_t(values[2]),std::int32_t(values[3])};return true;
}
// Canonical blocks and unique unit members are host-validated. Output storage
// must not alias inputs. Validation pass preserves outputs on every error.
inline std::uint32_t macro_translation_array(const Block* blocks,const Location* positions,std::uint64_t block_count,
 const std::uint32_t* members,std::uint32_t member_count,Location target,
 TrialMove* outputs,std::uint32_t capacity,std::uint32_t& status){
 status=0;if(!member_count){status=1;return 0;}
 if(member_count>capacity){status=2;return 0;}
 auto index=translation_index(blocks,block_count,members[0]);
 if(index==block_count){status=3;return 0;}auto root=positions[index];
 for(std::uint32_t i=0;i<member_count;++i){index=translation_index(blocks,block_count,members[i]);
  if(index==block_count){status=3;return 0;}Location candidate{};
  if(!translated_location(positions[index],target,root,candidate)){status=4;return 0;}
 }
 for(std::uint32_t i=0;i<member_count;++i){index=translation_index(blocks,block_count,members[i]);
  Location candidate{};translated_location(positions[index],target,root,candidate);outputs[i]={members[i],candidate};
 }
 return member_count;
}
}
