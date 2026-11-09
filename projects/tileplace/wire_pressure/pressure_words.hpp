#pragma once
#include "../hbm_abi/pressure_array_core.hpp"
namespace tileplace_wire {
using namespace tileplace_hbm;
inline std::int32_t signed_word(std::uint64_t x){auto v=std::uint32_t(x);return std::int32_t(v<=INT32_MAX?std::int64_t(v):std::int64_t(v)-4294967296LL);}
inline std::uint64_t segment(const std::uint64_t* lines,std::uint64_t lc,const std::uint64_t* entries,std::uint64_t ec,int axis,std::int32_t line,std::int32_t a,std::int32_t b,std::uint32_t& status){
 std::uint64_t low=0,high=lc;
 while(low<high){auto m=low+(high-low)/2;auto word=lines[4*m];auto ax=signed_word(word),ln=signed_word(word>>32);if(ax<axis||(ax==axis&&ln<line))low=m+1;else high=m;}
 if(low==lc)return 0;
 auto word=lines[4*low];if(signed_word(word)!=axis||signed_word(word>>32)!=line)return 0;
 auto total=lines[4*low+1],offset=lines[4*low+2],count=lines[4*low+3];
 if(offset>ec||count>ec-offset){status=1;return 0;}
 std::int32_t coordinates[2]={a<b?a:b,a<b?b:a};std::uint64_t values[2]{};
 for(unsigned k=0;k<2;++k){low=0;high=count;while(low<high){auto mid=low+(high-low)/2;if(signed_word(entries[2*(offset+mid)])<coordinates[k])low=mid+1;else high=mid;}
  values[k]=low==count?total:entries[2*(offset+low)+1];
 }
 if(values[1]<values[0]){status=2;return 0;}return values[1]-values[0];
}
// Host guarantees backing capacity and canonical records. No local copy or
// fixed line/entry capacity; indices are checked before record-word scaling.
inline PressureResult query(const std::uint64_t* lines,std::uint64_t lc,const std::uint64_t* entries,std::uint64_t ec,PressureQuery q){
 PressureResult r{};if(lc>UINT64_MAX/4||ec>UINT64_MAX/2){r.status=1;return r;}
 auto a=q.source,b=q.target;auto dx=std::int64_t(a.x)-b.x,dy=std::int64_t(a.y)-b.y;
 auto base=(std::uint64_t(dx<0?-dx:dx)+std::uint64_t(dy<0?-dy:dy))*65536;std::uint64_t v[2]{};
 for(unsigned i=0;i<2;++i){auto h=segment(lines,lc,entries,ec,0,i?b.y:a.y,a.x,b.x,r.status);auto t=segment(lines,lc,entries,ec,1,i?a.x:b.x,a.y,b.y,r.status);
  if(h>UINT64_MAX-base||t>UINT64_MAX-base-h){r.status=3;return r;}v[i]=base+h+t;
 }
 if(r.status)return r;
 r.horizontal=v[0];r.vertical=v[1];r.minimum=v[0]<v[1]?v[0]:v[1];return r;
}
}
