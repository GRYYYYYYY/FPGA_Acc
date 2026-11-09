#pragma once
#include "guard_words.hpp"
#include "../hbm_abi/occupancy_array.hpp"
namespace tileplace_wire_checks {
inline bool equal(tileplace_hbm::Location a,tileplace_hbm::Location b){return a.x==b.x&&a.y==b.y&&a.subtile==b.subtile&&a.layer==b.layer;}
// Canonical placement has unique locations. Status 1 rejects record scaling.
inline tileplace_hbm::Occupant occupant(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t count,const std::uint64_t* query,std::uint32_t& status){status=0;if(count>UINT64_MAX/8){status=1;return {0,0,0};}auto p=location(query);for(std::uint64_t i=0;i<count;++i)if(equal(location(positions+2*i),p))return {1,std::uint32_t(blocks[8*i]),std::uint32_t(blocks[8*i+7]>>32)};return {0,0,0};}
// Canonical units have unique IDs and positions; compare typed relative offsets in all four dimensions.
inline bool shape(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t count,const std::uint32_t* a,std::uint32_t na,const std::uint32_t* b,std::uint32_t nb,std::uint32_t& status){
 status=0;if(!na||!nb){status=1;return false;}if(na!=nb)return false;if(count>UINT64_MAX/8){status=3;return false;}
 auto ar=block_index(blocks,count,a[0]),br=block_index(blocks,count,b[0]);if(ar==count||br==count){status=2;return false;}
 for(std::uint32_t i=0;i<na;++i)if(block_index(blocks,count,a[i])==count||block_index(blocks,count,b[i])==count){status=2;return false;}
 auto root=location(positions+2*ar),other=location(positions+2*br);
 for(std::uint32_t i=0;i<na;++i){auto ai=block_index(blocks,count,a[i]);auto p=location(positions+2*ai);bool found=false;
 for(std::uint32_t j=0;j<nb;++j){auto bi=block_index(blocks,count,b[j]);auto q=location(positions+2*bi);found|=std::uint32_t(blocks[8*ai]>>32)==std::uint32_t(blocks[8*bi]>>32)&&std::int64_t(p.x)-root.x==std::int64_t(q.x)-other.x&&std::int64_t(p.y)-root.y==std::int64_t(q.y)-other.y&&std::int64_t(p.subtile)-root.subtile==std::int64_t(q.subtile)-other.subtile&&std::int64_t(p.layer)-root.layer==std::int64_t(q.layer)-other.layer;}
 if(!found)return false;
 }return true;
}
}
