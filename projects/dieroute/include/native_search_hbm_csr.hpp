#pragma once
#include <cstdint>
namespace dieroute {
enum class NativeCSRStatus {arc,end,budget,invalid};
struct NativeCSRArc {std::uint32_t node,edge,owner,membership;};
// Immutable native commit CSR/policy ABI. Caller provides an exclusive row
// cursor; this is resumable traversal, not dynamic cost or routing authority.
template<std::uint32_t MaximumNodes,std::uint64_t MaximumArcs>
NativeCSRStatus native_search_next_arc(const std::uint64_t* offsets,const std::uint64_t* arcs,
 const std::uint64_t* policy,std::uint32_t nodes,std::uint64_t arc_count,std::uint32_t dies,
 std::uint32_t source,std::uint32_t net,std::uint64_t max_visits,std::uint64_t& cursor,
 std::uint64_t& visited,NativeCSRArc& output){
 if(!nodes||nodes>MaximumNodes||arc_count>MaximumArcs||!dies||dies>8||source>=nodes||net==UINT32_MAX)return NativeCSRStatus::invalid;
 const auto begin=offsets[source],end=offsets[source+1];
 if(begin>end||end>arc_count||cursor<begin||cursor>end)return NativeCSRStatus::invalid;
 auto next=cursor;std::uint64_t count=0;
 while(next<end&&count<max_visits){
  const auto word=arcs[next];const auto dst=std::uint32_t(word),edge=std::uint32_t(word>>32);
  if(dst>=nodes||edge==UINT32_MAX)return NativeCSRStatus::invalid;
  const auto p=policy[dst];const auto mask=std::uint32_t((p>>32)&255);
  if(p>>41||!mask||mask>=(1u<<dies))return NativeCSRStatus::invalid;
  ++next;++count;
  if((p&(std::uint64_t(1)<<40))||(std::uint32_t(p)!=UINT32_MAX&&std::uint32_t(p)!=net))continue;
  std::uint32_t owner=0;while(!(mask&(1u<<owner)))++owner;
  output={dst,edge,owner,mask};cursor=next;visited=count;return NativeCSRStatus::arc;
 }
 cursor=next;visited=count;return next==end?NativeCSRStatus::end:NativeCSRStatus::budget;
}
}
