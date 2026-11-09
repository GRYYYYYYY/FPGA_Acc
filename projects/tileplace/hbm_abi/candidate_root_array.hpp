#pragma once
#include "snapshot_abi.hpp"
namespace tileplace_hbm {
// Input sites are canonical, unique records validated by the host.
inline std::int32_t root_page(std::int32_t value,std::int32_t size){
 auto q=value/size;return value%size<0?q-1:q;
}
inline std::uint64_t root_distance(Location a,Location b){
 auto x=std::int64_t(a.x)-b.x,y=std::int64_t(a.y)-b.y;
 return std::uint64_t(x<0?-x:x)+std::uint64_t(y<0?-y:y);
}
inline bool root_less(Location a,Location b,Location source){
 auto da=root_distance(a,source),db=root_distance(b,source);
 if(da!=db)return da<db;
 if(a.layer!=b.layer)return a.layer<b.layer;
 if(a.y!=b.y)return a.y<b.y;
 if(a.x!=b.x)return a.x<b.x;
 return a.subtile<b.subtile;
}
inline std::uint32_t candidate_root_array(const Site* sites,std::uint64_t count,
 Location source,std::uint32_t type,std::int32_t width,std::int32_t height,
 std::uint32_t limit,Location* outputs,std::uint32_t capacity,std::uint32_t& status){
 status=0;
 if(width<=0||height<=0){status=1;return 0;}
 if(limit>capacity){status=2;return 0;}
 if(!limit)return 0;
 auto px=root_page(source.x,width),py=root_page(source.y,height);
 std::uint32_t size=0;
 for(std::uint64_t i=0;i<count;++i){
  auto p=sites[i].location;
  if(sites[i].type_id!=type||p.layer!=source.layer)continue;
  auto dx=std::int64_t(root_page(p.x,width))-px,dy=std::int64_t(root_page(p.y,height))-py;
  if(dx<-1||dx>1||dy<-1||dy>1)continue;
  std::uint32_t index=0;while(index<size&&!root_less(p,outputs[index],source))++index;
  if(index==limit)continue;
  auto end=size<limit?size:size-1;
  for(auto j=end;j>index;--j)outputs[j]=outputs[j-1];
  outputs[index]=p;if(size<limit)++size;
 }
 return size;
}
}
