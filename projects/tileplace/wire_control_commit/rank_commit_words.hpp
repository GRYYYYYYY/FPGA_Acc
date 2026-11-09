#pragma once
#include "control_commit_words.hpp"
#include "../wire_dedup/dedup_words.hpp"
namespace tileplace_wire_control_commit {
// Input transaction13 identities and conflict pools share backing with forbidden.
// Compose per-group best -> identity dedup -> conflicts -> atomic commit.
// Output indices refer to original input records, in selection order.
// Scratch buffers: best7/gathered/group_indices/unique_indices/compact13/order/
// selected each reserve at least group_count records; no aliases. Positions are
// untouched on any failure. All other scratch is discardable.
// Stages 1 input/best, 2 dedup, 3 conflict selection, 4 commit.
inline Result rank_commit(const std::uint64_t* records,std::uint32_t count,
 const std::uint64_t* groups,std::uint32_t group_count,
 const std::uint64_t* forbidden,std::uint32_t forbidden_count,
 const std::uint8_t* kinds,std::uint64_t kind_count,
 const std::uint64_t* units,std::uint64_t unit_count,
 const std::uint32_t* members,std::uint64_t member_count,
 const std::uint64_t* trials,std::uint64_t trial_count,
 const std::uint64_t* sites,std::uint64_t site_count,
 const std::uint32_t* nets,std::uint64_t net_count,
 const std::uint32_t* conflict_units,std::uint64_t conflict_unit_count,
 const std::uint64_t* blocks,std::uint64_t block_count,std::uint64_t* positions,
 std::uint64_t* candidates,std::uint32_t candidate_capacity,
 std::uint64_t* best7,std::uint64_t* compact13,
 std::uint32_t* group_indices,std::uint32_t* gathered,
 std::uint32_t* unique_indices,std::uint32_t* order,std::uint32_t* selected,
 std::uint32_t scratch_capacity){
 if(count>candidate_capacity||group_count>scratch_capacity)return {1,2,0,0};
 for(std::uint32_t i=0;i<count;++i)for(unsigned j=0;j<7;++j)candidates[7ULL*i+j]=records[13ULL*i+j];
 unsigned status;
 tileplace_wire_best::best(candidates,count,groups,group_count,forbidden,forbidden_count,kinds,kind_count,units,unit_count,members,member_count,trials,trial_count,group_indices,scratch_capacity,status);
 if(status)return {1,status,0,0};
 unsigned gathered_count=0;
 for(std::uint32_t g=0;g<group_count;++g){auto i=group_indices[g];if(i==UINT32_MAX)continue;gathered[gathered_count]=i;
  for(unsigned j=0;j<7;++j)best7[7ULL*gathered_count+j]=candidates[7ULL*i+j];
  ++gathered_count;
 }
 auto n=tileplace_wire_dedup::dedup(best7,gathered_count,kinds,kind_count,units,unit_count,members,member_count,trials,trial_count,unique_indices,scratch_capacity,status);
 if(status)return {2,status,0,0};
 for(std::uint32_t i=0;i<n;++i){auto original=gathered[unique_indices[i]];
  for(unsigned j=0;j<13;++j)compact13[13ULL*i+j]=records[13ULL*original+j];
 }
 auto accepted=tileplace_wire_transactions::select(compact13,n,kinds,kind_count,units,unit_count,members,member_count,trials,trial_count,sites,site_count,nets,net_count,conflict_units,conflict_unit_count,order,scratch_capacity,selected,scratch_capacity,status);
 if(status)return {3,status,0,0};
 auto moved=tileplace_wire_commit::commit(compact13,n,selected,accepted,trials,trial_count,blocks,block_count,positions,status);
 if(status)return {4,status,0,0};
 for(std::uint32_t i=0;i<accepted;++i)selected[i]=gathered[unique_indices[selected[i]]];
 return {0,0,accepted,moved,n};
}
}
