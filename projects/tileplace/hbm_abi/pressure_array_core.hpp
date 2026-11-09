#pragma once
#include "snapshot_abi.hpp"
namespace tileplace_hbm {
// Host canonical validation precedes this array-only data plane.
struct PressureResult {std::uint64_t horizontal,vertical,minimum;std::uint32_t status,reserved;};
struct PressureQuery {Location source,target;};
inline std::uint64_t array_segment(const PrefixLine* lines,std::uint64_t line_count,
 const PrefixEntry* entries,std::uint64_t entry_count,int axis,std::int32_t line,
 std::int32_t a,std::int32_t b,std::uint32_t& status) {
 std::uint64_t low=0,high=line_count;
 while(low<high){auto mid=low+(high-low)/2;const auto& item=lines[mid];
  if(item.axis<axis||(item.axis==axis&&item.line<line))low=mid+1;else high=mid;
 }
 if(low==line_count||lines[low].axis!=axis||lines[low].line!=line)return 0;
 const auto& record=lines[low];
 if(!valid_range(record.entries,entry_count)){status=1;return 0;}
 std::int32_t coordinates[2]={a<b?a:b,a<b?b:a};std::uint64_t values[2]{};
 for(unsigned k=0;k<2;++k){low=0;high=record.entries.count;
  while(low<high){auto mid=low+(high-low)/2;
   if(entries[record.entries.offset+mid].coordinate<coordinates[k])low=mid+1;else high=mid;
  }
  values[k]=low==record.entries.count?record.total_pressure:entries[record.entries.offset+low].cumulative_before;
 }
 if(values[1]<values[0]){status=2;return 0;}
 return values[1]-values[0];
}
inline PressureResult pressure_array_query(const PrefixLine* lines,std::uint64_t line_count,
 const PrefixEntry* entries,std::uint64_t entry_count,PressureQuery query) {
 PressureResult out{};auto a=query.source,b=query.target;
 auto dx=std::int64_t(a.x)-b.x,dy=std::int64_t(a.y)-b.y;
 auto base=(std::uint64_t(dx<0?-dx:dx)+std::uint64_t(dy<0?-dy:dy))*65536;
 std::uint64_t values[2]{};
 for(unsigned i=0;i<2;++i){
  auto h=array_segment(lines,line_count,entries,entry_count,0,i?b.y:a.y,a.x,b.x,out.status);
  auto v=array_segment(lines,line_count,entries,entry_count,1,i?a.x:b.x,a.y,b.y,out.status);
  if(h>UINT64_MAX-base || v>UINT64_MAX-base-h){out.status=3;return out;}
  values[i]=base+h+v;
 }
 if(out.status)return out;
 out.horizontal=values[0];out.vertical=values[1];out.minimum=values[0]<values[1]?values[0]:values[1];return out;
}
extern "C" void tileplace_pressure_array(const PrefixLine* lines,const PrefixEntry* entries,
 const PressureQuery* queries,PressureResult* outputs,std::uint64_t line_count,
 std::uint64_t entry_count,std::uint32_t query_count);
}
