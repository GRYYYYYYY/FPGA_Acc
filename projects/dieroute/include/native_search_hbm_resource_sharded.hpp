#pragma once
#include "native_search_hbm_resource.hpp"
namespace dieroute {
// Read-only native commit owner shards. Requires exclusive immutable authority
// handoff through completion. Session/revision checks are not a concurrent
// snapshot protocol; membership-chain validation remains the authority's job.
template<std::uint32_t MaximumShard>
NativeResourceReadStatus native_search_read_resource_sharded(const std::uint64_t* policy,
 const SummaryWord* resources0,const SummaryWord* resources1,const SummaryWord* resources2,const SummaryWord& control,std::uint32_t nodes,std::uint32_t dies,
 std::uint32_t shard_capacity,std::uint32_t tree_capacity,std::uint32_t node,
 std::uint64_t session,std::uint64_t revision,std::uint64_t epoch,NativeSearchResourceObservation& output){
 if(!nodes||node>=nodes||!dies||dies>3||!shard_capacity||shard_capacity>MaximumShard||
    (shard_capacity&(shard_capacity-1))||!tree_capacity||!session||!epoch||
    control.w[0]!=session||control.w[1]!=revision||control.w[5]!=(nodes|(std::uint64_t(dies)<<32))||
    std::uint32_t(control.w[6])!=shard_capacity||control.w[7]!=tree_capacity)return NativeResourceReadStatus::invalid;
 auto p=policy[node];auto mask=std::uint32_t((p>>32)&255);
 if(p>>41||!mask||(mask>>dies))return NativeResourceReadStatus::invalid;
 unsigned owner=0;for(unsigned d=0;d<3;++d)if(mask&(1u<<d)){owner=d;break;}
 const auto hash=(node*UINT32_C(2654435761))&(shard_capacity-1);
 for(std::uint32_t probe=0;probe<shard_capacity;++probe){const auto index=(hash+probe)&(shard_capacity-1);auto r=owner==0?resources0[index]:owner==1?resources1[index]:resources2[index];
  if(r.w[0]>session)return NativeResourceReadStatus::invalid;
  if(r.w[0]!=session){output={node,0,0,0,session,epoch,owner,0};return NativeResourceReadStatus::absent;}
  if(r.w[4]>>40||std::uint32_t(r.w[4])>=nodes||r.w[2]==UINT64_MAX||r.w[6]||r.w[7]||r.w[1]>tree_capacity||((r.w[1]==0)!=(r.w[5]==UINT64_MAX)))return NativeResourceReadStatus::invalid;
  if(std::uint32_t(r.w[4])==node){if(r.w[4]!=(node|(std::uint64_t(mask)<<32)))return NativeResourceReadStatus::invalid;
   output={node,r.w[3],r.w[1],r.w[2],session,epoch,owner,0};return NativeResourceReadStatus::present;
  }
 }
 output={node,0,0,0,session,epoch,owner,0};return NativeResourceReadStatus::absent;
}
}
