#pragma once
#include "../hbm_abi/trial_legality_array.hpp"
namespace tileplace_transaction_array {
using tileplace_hbm::Range;
struct Identity {Range kind,units,trial;};
template<class T,class Compare>
inline int range_compare(const T* values,Range a,Range b,Compare compare){
 auto count=a.count<b.count?a.count:b.count;
 for(std::uint64_t i=0;i<count;++i){auto result=compare(values[a.offset+i],values[b.offset+i]);if(result)return result;}
 return a.count<b.count?-1:a.count>b.count?1:0;
}
inline int unsigned_compare(std::uint32_t a,std::uint32_t b){return a<b?-1:a>b?1:0;}
// Caller validates every referenced range and canonicalizes unit/trial records.
// Kind bytes preserve full string ordering; no fixed list of candidate kinds.
inline int identity_compare(Identity a,Identity b,const std::uint8_t* kinds,
 const Range* units,const std::uint32_t* members,const tileplace_hbm::TrialMove* trials){
 auto result=range_compare(kinds,a.kind,b.kind,[](std::uint8_t x,std::uint8_t y){return unsigned_compare(x,y);});
 if(result)return result;
 result=range_compare(units,a.units,b.units,[&](Range x,Range y){return range_compare(members,x,y,unsigned_compare);});
 if(result)return result;
 return range_compare(trials,a.trial,b.trial,[](tileplace_hbm::TrialMove x,tileplace_hbm::TrialMove y){
  auto order=unsigned_compare(x.id,y.id);if(order)return order;
  if(tileplace_hbm::location_less(x.target,y.target))return -1;
  if(tileplace_hbm::location_less(y.target,x.target))return 1;
  return 0;
 });
}
}
