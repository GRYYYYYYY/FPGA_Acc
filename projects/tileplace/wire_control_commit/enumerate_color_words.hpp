#pragma once
#include "enumerate_descriptors.hpp"
namespace tileplace_wire_control_commit {
// Enumerate the externally validated eligible list in its original order. Empty
// groups (including fixed units) remain in place for eligible-stat semantics.
// Status6 group capacity; downstream must discard all scratch on any error.
inline void enumerate_color(const std::uint32_t* eligible,unsigned eligible_count,const std::uint64_t* units,std::uint32_t uc,const std::uint32_t* members,const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,const std::uint64_t* sites,std::uint64_t sc,int width,int height,unsigned limit,unsigned chain_limit,std::uint64_t* roots,unsigned root_capacity,std::uint64_t* chain_roots,unsigned chain_capacity,std::uint64_t* first,std::uint64_t* second,std::uint64_t* merged,unsigned move_capacity,std::uint64_t* descriptors,unsigned descriptor_capacity,std::uint32_t* output_owners,unsigned owner_capacity,std::uint64_t* output_trials,unsigned trial_capacity,unsigned& emitted,unsigned& owner_used,unsigned& trial_used,bool& overflow,unsigned& status,std::uint64_t* groups,unsigned group_capacity){
 status=0;
 if(eligible_count>group_capacity){status=6;return;}
 for(unsigned i=0;i<eligible_count;++i)if(eligible[i]>=uc){status=1;return;}
 for(unsigned i=0;i<eligible_count;++i){auto begin=emitted;
  tileplace_wire_descriptor_enumerator::enumerate(eligible[i],units,uc,members,blocks,positions,bc,sites,sc,width,height,limit,chain_limit,roots,root_capacity,chain_roots,chain_capacity,first,second,merged,move_capacity,descriptors,descriptor_capacity,output_owners,owner_capacity,output_trials,trial_capacity,emitted,owner_used,trial_used,overflow,status);
  if(status)return;
  groups[2ULL*i]=begin;groups[2ULL*i+1]=emitted-begin;
 }
}
}
