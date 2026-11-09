#pragma once
#include "identity_words.hpp"
namespace tileplace_wire_transactions {
inline std::int64_t score(std::uint64_t word){return word<=INT64_MAX?std::int64_t(word):-1-std::int64_t(UINT64_MAX-word);}
template<class Equal> inline bool overlap(Range a,Range b,Equal equal){for(std::uint64_t i=0;i<a.count;++i)for(std::uint64_t j=0;j<b.count;++j)if(equal(a.offset+i,b.offset+j))return true;return false;}
// 13-word record: score, six identity words, site/net/unit conflict ranges.
// Host supplies canonical full identities/unit IDs and distinct output buffers.
inline std::uint32_t select(const std::uint64_t* records,std::uint32_t count,const std::uint8_t* kinds,std::uint64_t kc,const std::uint64_t* identity_units,std::uint64_t ic,const std::uint32_t* members,std::uint64_t mc,const std::uint64_t* trials,std::uint64_t tc,const std::uint64_t* sites,std::uint64_t sc,const std::uint32_t* nets,std::uint64_t nc,const std::uint32_t* units,std::uint64_t uc,std::uint32_t* order,std::uint32_t oc,std::uint32_t* selected,std::uint32_t cap,std::uint32_t& status){
 status=0;if(count>oc||count>cap){status=2;return 0;}
 if(ic>UINT64_MAX/2||tc>UINT64_MAX/3||sc>UINT64_MAX/2){status=3;return 0;}
 for(std::uint32_t i=0;i<count;++i){auto r=records+13ULL*i;if(!tileplace_hbm::valid_range(range(r+7),sc)||!tileplace_hbm::valid_range(range(r+9),nc)||!tileplace_hbm::valid_range(range(r+11),uc)){status=1;return 0;}}
 for(std::uint64_t i=0;i<ic;++i)if(!tileplace_hbm::valid_range(range(identity_units+2*i),mc)){status=3;return 0;}
 for(std::uint32_t i=0;i<count;++i){auto r=records+13ULL*i;if(!tileplace_hbm::valid_range(range(r+1),kc)||!tileplace_hbm::valid_range(range(r+3),ic)||!tileplace_hbm::valid_range(range(r+5),tc)){status=3;return 0;}}
 for(std::uint32_t i=0;i<count;++i){auto j=i;auto a=records+13ULL*i;while(j){auto b=records+13ULL*order[j-1];if(score(a[0])>score(b[0])||(score(a[0])==score(b[0])&&identity(a+1,b+1,kinds,identity_units,members,trials)>=0))break;order[j]=order[j-1];--j;}order[j]=i;}
 std::uint32_t size=0;
 for(std::uint32_t i=0;i<count;++i){auto index=order[i];auto a=records+13ULL*index;if(score(a[0])>=0)continue;bool conflict=false;
  for(std::uint32_t j=0;j<size;++j){auto b=records+13ULL*selected[j];conflict|=overlap(range(a+7),range(b+7),[&](std::uint64_t x,std::uint64_t y){return sites[2*x]==sites[2*y]&&sites[2*x+1]==sites[2*y+1];})||overlap(range(a+9),range(b+9),[&](std::uint64_t x,std::uint64_t y){return nets[x]==nets[y];})||overlap(range(a+11),range(b+11),[&](std::uint64_t x,std::uint64_t y){return units[x]==units[y];});}
  if(!conflict)selected[size++]=index;
 }return size;
}
}
