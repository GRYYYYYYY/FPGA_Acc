#pragma once
#include "../hbm_abi/snapshot_abi.hpp"
namespace tileplace_wire_transactions {
using tileplace_hbm::Range;
inline Range range(const std::uint64_t* words){return {words[0],words[1]};}
template<class Compare> inline int lex(Range a,Range b,Compare compare){auto count=a.count<b.count?a.count:b.count;for(std::uint64_t i=0;i<count;++i){auto r=compare(a.offset+i,b.offset+i);if(r)return r;}return a.count<b.count?-1:a.count>b.count?1:0;}
inline int unsigned_order(std::uint32_t a,std::uint32_t b){return a<b?-1:a>b?1:0;}
inline std::int64_t signed32(std::uint64_t word){auto v=std::uint32_t(word);return v<=INT32_MAX?std::int64_t(v):std::int64_t(v)-4294967296LL;}
// Host validates all ranges, record scaling and canonical full identities.
// Six-word identity: kind range, nested unit range, trial range.
inline int identity(const std::uint64_t* a,const std::uint64_t* b,const std::uint8_t* kinds,const std::uint64_t* units,const std::uint32_t* members,const std::uint64_t* trials){
 auto r=lex(range(a),range(b),[&](std::uint64_t x,std::uint64_t y){return unsigned_order(kinds[x],kinds[y]);});if(r)return r;
 r=lex(range(a+2),range(b+2),[&](std::uint64_t x,std::uint64_t y){return lex(range(units+2*x),range(units+2*y),[&](std::uint64_t i,std::uint64_t j){return unsigned_order(members[i],members[j]);});});if(r)return r;
 return lex(range(a+4),range(b+4),[&](std::uint64_t x,std::uint64_t y){auto order=unsigned_order(std::uint32_t(trials[3*x]),std::uint32_t(trials[3*y]));if(order)return order;
  for(unsigned k=0;k<4;++k){auto shift=(k%2)*32;auto p=signed32(trials[3*x+1+k/2]>>shift),q=signed32(trials[3*y+1+k/2]>>shift);if(p<q)return -1;if(p>q)return 1;}return 0;
 });
}
}
