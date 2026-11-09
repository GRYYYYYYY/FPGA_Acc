#pragma once
#include "../wire_candidates/translation_words.hpp"
namespace tileplace_wire_control {
// Unit ABI: member offset/count then fixed flag/reserved word and reserved word.
// Eligible includes fixed units, matching native eligible statistics; generation skips them later.
// Status 1 dimensions/color, 2 unit CSR/empty, 3 unknown block, 4 capacity, 5 scaling.
inline bool focus_contains(const std::uint32_t* focus,std::uint64_t count,std::uint32_t id){std::uint64_t lo=0,hi=count;while(lo<hi){auto mid=lo+(hi-lo)/2;if(focus[mid]<id)lo=mid+1;else hi=mid;}return lo<count&&focus[lo]==id;}
inline bool matches(const std::uint64_t* unit,const std::uint32_t* members,const std::uint32_t* focus,std::uint64_t fc,const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,std::int32_t width,std::int32_t height,unsigned color){
 bool focused=!fc;for(std::uint64_t j=0;j<unit[1];++j)focused|=focus_contains(focus,fc,members[unit[0]+j]);if(!focused)return false;
 auto index=tileplace_wire_candidates::block_index(blocks,bc,members[unit[0]]);auto p=tileplace_wire_candidates::location(positions+2*index);auto x=tileplace_hbm::root_page(p.x,width),y=tileplace_hbm::root_page(p.y,height);return unsigned((std::uint32_t(x)&1)*2+(std::uint32_t(y)&1))==color;
}
inline std::uint32_t eligible(const std::uint64_t* units,std::uint64_t uc,const std::uint32_t* members,std::uint64_t mc,const std::uint32_t* focus,std::uint64_t fc,const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,std::int32_t width,std::int32_t height,unsigned color,std::uint32_t* output,std::uint32_t capacity,std::uint32_t& status){
 status=0;if(width<=0||height<=0||color>=4){status=1;return 0;}if(uc>UINT32_MAX||uc>UINT64_MAX/4||bc>UINT64_MAX/8){status=5;return 0;}
 for(std::uint64_t i=0;i<uc;++i){auto u=units+4*i;if(!u[1]||u[0]>mc||u[1]>mc-u[0]){status=2;return 0;}for(std::uint64_t j=0;j<u[1];++j)if(tileplace_wire_candidates::block_index(blocks,bc,members[u[0]+j])==bc){status=3;return 0;}}
 std::uint64_t total=0;for(std::uint64_t i=0;i<uc;++i)total+=matches(units+4*i,members,focus,fc,blocks,positions,bc,width,height,color);if(total>capacity){status=4;return 0;}
 std::uint32_t size=0;for(std::uint64_t i=0;i<uc;++i)if(matches(units+4*i,members,focus,fc,blocks,positions,bc,width,height,color))output[size++]=i;return size;
}
}
