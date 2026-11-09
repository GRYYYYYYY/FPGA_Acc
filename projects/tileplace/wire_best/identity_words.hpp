#pragma once
#include "../hbm_abi/snapshot_abi.hpp"
namespace tileplace_wire_best {
using tileplace_hbm::Range;
inline Range range(const std::uint64_t* words){return {words[0],words[1]};}
template<class Compare> inline int lex(Range a,Range b,Compare compare){auto count=a.count<b.count?a.count:b.count;for(std::uint64_t i=0;i<count;++i){auto r=compare(a.offset+i,b.offset+i);if(r)return r;}return a.count<b.count?-1:a.count>b.count?1:0;}
inline int unsigned_order(std::uint32_t a,std::uint32_t b){return a<b?-1:a>b?1:0;}
inline std::int64_t signed32(std::uint64_t word){auto v=std::uint32_t(word);return v<=INT32_MAX?std::int64_t(v):std::int64_t(v)-4294967296LL;}
// Host validates all ranges, record scaling and canonical full identities.
// Six-word identity: kind range, nested unit range, trial range.
inline int identity(const std::uint64_t* a,const std::uint64_t* b,const std::uint8_t* kinds,const std::uint64_t* units,const std::uint32_t* members,const std::uint64_t* trials){
 auto x=range(a),y=range(b);auto count=x.count<y.count?x.count:y.count;
 for(std::uint64_t i=0;i<count;++i){auto r=unsigned_order(kinds[x.offset+i],kinds[y.offset+i]);if(r)return r;}if(x.count!=y.count)return x.count<y.count?-1:1;
 x=range(a+2);y=range(b+2);count=x.count<y.count?x.count:y.count;
 for(std::uint64_t i=0;i<count;++i){auto u=range(units+2*(x.offset+i)),v=range(units+2*(y.offset+i));auto n=u.count<v.count?u.count:v.count;for(std::uint64_t j=0;j<n;++j){auto r=unsigned_order(members[u.offset+j],members[v.offset+j]);if(r)return r;}if(u.count!=v.count)return u.count<v.count?-1:1;}
 if(x.count!=y.count)return x.count<y.count?-1:1;
 x=range(a+4);y=range(b+4);count=x.count<y.count?x.count:y.count;
 for(std::uint64_t i=0;i<count;++i){auto p=trials+3*(x.offset+i),q=trials+3*(y.offset+i);auto r=unsigned_order(std::uint32_t(p[0]),std::uint32_t(q[0]));if(r)return r;
 for(unsigned k=0;k<4;++k){auto shift=(k%2)*32;auto m=signed32(p[1+k/2]>>shift),n=signed32(q[1+k/2]>>shift);if(m!=n)return m<n?-1:1;}}
 return x.count<y.count?-1:x.count>y.count?1:0;
}
}
