#pragma once
#include "../hbm_abi/snapshot_abi.hpp"
namespace tileplace_transaction_array {
using tileplace_hbm::Range;
using tileplace_hbm::Location;
struct Record {std::int64_t score;std::uint64_t identity_rank;Range sites,nets,units;};
inline bool same(Location a,Location b){return a.x==b.x&&a.y==b.y&&a.subtile==b.subtile&&a.layer==b.layer;}
template<class T,class Equal>
inline bool overlap(const T* data,Range a,Range b,Equal equal){
 for(std::uint64_t i=0;i<a.count;++i)for(std::uint64_t j=0;j<b.count;++j)if(equal(data[a.offset+i],data[b.offset+j]))return true;
 return false;
}
// Host assigns unique ranks in full proposal-identity order and canonical unit
// IDs. Scratch and output buffers must be distinct and have count capacity.
// Validate all ranges/capacities before writing either caller buffer.
inline std::uint32_t select(const Record* records,std::uint32_t count,
 const Location* sites,std::uint64_t site_count,const std::uint32_t* nets,std::uint64_t net_count,
 const std::uint32_t* units,std::uint64_t unit_count,std::uint32_t* order,std::uint32_t order_capacity,
 std::uint32_t* selected,std::uint32_t selected_capacity,std::uint32_t& status){
 status=0;if(count>order_capacity||count>selected_capacity){status=2;return 0;}
 for(std::uint32_t i=0;i<count;++i)if(!tileplace_hbm::valid_range(records[i].sites,site_count)||!tileplace_hbm::valid_range(records[i].nets,net_count)||!tileplace_hbm::valid_range(records[i].units,unit_count)){status=1;return 0;}
 for(std::uint32_t i=0;i<count;++i){auto j=i;
  while(j){const auto& a=records[i];const auto& b=records[order[j-1]];
   if(a.score>b.score||(a.score==b.score&&a.identity_rank>=b.identity_rank))break;
   order[j]=order[j-1];--j;
  }order[j]=i;
 }
 std::uint32_t size=0;
 for(std::uint32_t i=0;i<count;++i){auto index=order[i];const auto& a=records[index];if(a.score>=0)continue;bool conflict=false;
  for(std::uint32_t j=0;j<size;++j){const auto& b=records[selected[j]];
   conflict|=overlap(sites,a.sites,b.sites,[](Location x,Location y){return same(x,y);})||
    overlap(nets,a.nets,b.nets,[](std::uint32_t x,std::uint32_t y){return x==y;})||
    overlap(units,a.units,b.units,[](std::uint32_t x,std::uint32_t y){return x==y;});
  }
  if(!conflict)selected[size++]=index;
 }
 return size;
}
}
