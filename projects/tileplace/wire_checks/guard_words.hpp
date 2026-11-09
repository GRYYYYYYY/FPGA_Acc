#pragma once
#include "../wire_candidates/translation_words.hpp"
namespace tileplace_wire_checks {
using tileplace_wire_candidates::location;
using tileplace_wire_candidates::block_index;
inline bool position(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t count,const std::uint64_t* moves,std::uint32_t size,std::uint32_t id,tileplace_hbm::Location& out){auto index=block_index(blocks,count,id);if(index==count)return false;out=location(positions+2*index);for(std::uint32_t i=0;i<size;++i)if(std::uint32_t(moves[3ULL*i])==id)out=location(moves+3ULL*i+1);return true;}
// Guard record: packed source/sink IDs then maximum Manhattan distance.
// Host validates unique trial IDs, canonical blocks, and backing capacities.
inline bool guards(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t count,const std::uint64_t* moves,std::uint32_t size,const std::uint64_t* constraints,std::uint64_t gc,std::uint32_t& status){
 status=0;if(count>UINT64_MAX/8||gc>UINT64_MAX/2){status=3;return false;}
 for(std::uint32_t i=0;i<size;++i)if(block_index(blocks,count,std::uint32_t(moves[3ULL*i]))==count){status=1;return false;}
 for(std::uint64_t i=0;i<gc;++i){auto source=std::uint32_t(constraints[2*i]),sink=std::uint32_t(constraints[2*i]>>32);bool changed=false;for(std::uint32_t j=0;j<size;++j){auto id=std::uint32_t(moves[3ULL*j]);changed|=id==source||id==sink;}if(!changed)continue;
 tileplace_hbm::Location a{},b{};if(!position(blocks,positions,count,moves,size,source,a)||!position(blocks,positions,count,moves,size,sink,b)){status=2;return false;}if(tileplace_hbm::root_distance(a,b)>constraints[2*i+1])return false;
 }return true;
}
}
