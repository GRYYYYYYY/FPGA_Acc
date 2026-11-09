#pragma once
#include "selection.hpp"
#include "identity.hpp"
namespace tileplace_transaction_array {
struct IdentityRecord {std::int64_t score;Identity identity;Range sites,nets,units;};
// Host supplies canonical full identities and canonical unit conflict IDs. Scratch and output buffers must be distinct and have count capacity.
// Validate all ranges/capacities before writing either caller buffer.
inline std::uint32_t select_identity(const IdentityRecord* records,std::uint32_t count,
 const std::uint8_t* kinds,std::uint64_t kind_count,const Range* identity_units,std::uint64_t identity_unit_count,
 const std::uint32_t* members,std::uint64_t member_count,const tileplace_hbm::TrialMove* trials,std::uint64_t trial_count,
 const Location* sites,std::uint64_t site_count,const std::uint32_t* nets,std::uint64_t net_count,
 const std::uint32_t* units,std::uint64_t unit_count,std::uint32_t* order,std::uint32_t order_capacity,
 std::uint32_t* selected,std::uint32_t selected_capacity,std::uint32_t& status){
 status=0;if(count>order_capacity||count>selected_capacity){status=2;return 0;}
 for(std::uint32_t i=0;i<count;++i)if(!tileplace_hbm::valid_range(records[i].sites,site_count)||!tileplace_hbm::valid_range(records[i].nets,net_count)||!tileplace_hbm::valid_range(records[i].units,unit_count)){status=1;return 0;}
 for(std::uint64_t i=0;i<identity_unit_count;++i)if(!tileplace_hbm::valid_range(identity_units[i],member_count)){status=3;return 0;}
 for(std::uint32_t i=0;i<count;++i){const auto& id=records[i].identity;
  if(!tileplace_hbm::valid_range(id.kind,kind_count)||!tileplace_hbm::valid_range(id.units,identity_unit_count)||!tileplace_hbm::valid_range(id.trial,trial_count)){status=3;return 0;}
 }
 for(std::uint32_t i=0;i<count;++i){auto j=i;
  while(j){const auto& a=records[i];const auto& b=records[order[j-1]];
   if(a.score>b.score||(a.score==b.score&&identity_compare(a.identity,b.identity,kinds,identity_units,members,trials)>=0))break;
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
