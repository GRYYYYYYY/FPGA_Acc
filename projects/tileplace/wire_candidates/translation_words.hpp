#pragma once
#include "root_words.hpp"
#include "../hbm_abi/macro_translation_array.hpp"
namespace tileplace_wire_candidates {
inline std::uint64_t block_index(const std::uint64_t* blocks,std::uint64_t count,std::uint32_t id){std::uint64_t low=0,high=count;while(low<high){auto mid=low+(high-low)/2;if(std::uint32_t(blocks[8*mid])<id)low=mid+1;else high=mid;}return low<count&&std::uint32_t(blocks[8*low])==id?low:count;}
// Host validates sorted unique blocks/members and disjoint backed arrays.
// Output trial records are ID plus two location words. Two passes preserve output on errors.
inline std::uint32_t translate(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t count,const std::uint32_t* members,std::uint32_t size,const std::uint64_t* target_words,std::uint64_t* output,std::uint32_t capacity,std::uint32_t& status){
 status=0;if(!size){status=1;return 0;}if(size>capacity){status=2;return 0;}if(count>UINT64_MAX/8){status=5;return 0;}
 auto index=block_index(blocks,count,members[0]);if(index==count){status=3;return 0;}auto root=location(positions+2*index),target=location(target_words);
 for(std::uint32_t i=0;i<size;++i){index=block_index(blocks,count,members[i]);if(index==count){status=3;return 0;}tileplace_hbm::Location p{};if(!tileplace_hbm::translated_location(location(positions+2*index),target,root,p)){status=4;return 0;}}
 for(std::uint32_t i=0;i<size;++i){index=block_index(blocks,count,members[i]);tileplace_hbm::Location p{};tileplace_hbm::translated_location(location(positions+2*index),target,root,p);output[3ULL*i]=members[i];store(output+3ULL*i+1,p);}return size;
}
}
