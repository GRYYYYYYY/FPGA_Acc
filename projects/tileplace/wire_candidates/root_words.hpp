#pragma once
#include "../hbm_abi/candidate_root_array.hpp"
namespace tileplace_wire_candidates {
inline std::int32_t signed32(std::uint64_t w){auto x=std::uint32_t(w);return x<=INT32_MAX?std::int32_t(x):std::int32_t(std::int64_t(x)-4294967296LL);}
inline tileplace_hbm::Location location(const std::uint64_t* w){return {signed32(w[0]),signed32(w[0]>>32),signed32(w[1]),signed32(w[1]>>32)};}
inline void store(std::uint64_t* w,tileplace_hbm::Location p){w[0]=std::uint32_t(p.x)|(std::uint64_t(std::uint32_t(p.y))<<32);w[1]=std::uint32_t(p.subtile)|(std::uint64_t(std::uint32_t(p.layer))<<32);}
// Canonical unique ABI Site records; caller owns backing capacities and disjoint buffers.
// Status 1: invalid page dimensions; 2: output capacity; 3: record scaling.
inline std::uint32_t roots(const std::uint64_t* sites,std::uint64_t count,const std::uint64_t* source_words,std::uint32_t type,std::int32_t width,std::int32_t height,std::uint32_t limit,std::uint64_t* output,std::uint32_t capacity,std::uint32_t& status){
 status=0;if(width<=0||height<=0){status=1;return 0;}if(limit>capacity){status=2;return 0;}if(count>UINT64_MAX/4){status=3;return 0;}if(!limit)return 0;
 auto source=location(source_words);auto px=tileplace_hbm::root_page(source.x,width),py=tileplace_hbm::root_page(source.y,height);std::uint32_t size=0;
 for(std::uint64_t i=0;i<count;++i){auto p=location(sites+4*i);if(std::uint32_t(sites[4*i+2])!=type||p.layer!=source.layer)continue;
 auto dx=std::int64_t(tileplace_hbm::root_page(p.x,width))-px,dy=std::int64_t(tileplace_hbm::root_page(p.y,height))-py;if(dx<-1||dx>1||dy<-1||dy>1)continue;
 std::uint32_t index=0;while(index<size&&!tileplace_hbm::root_less(p,location(output+2ULL*index),source))++index;if(index==limit)continue;
 auto end=size<limit?size:size-1;for(auto j=end;j>index;--j){output[2ULL*j]=output[2ULL*(j-1)];output[2ULL*j+1]=output[2ULL*(j-1)+1];}store(output+2ULL*index,p);if(size<limit)++size;
 }return size;
}
}
