#pragma once
#include "rank_commit_words.hpp"
namespace tileplace_wire_control_commit {
// Full descriptors -> identities -> forbidden/per-group best -> dedup -> conflicts -> commit.
// Groups reference descriptor indices; forbidden identities are selected descriptor indices
// in the same encoded pool (groups should exclude placeholder forbidden descriptors).
// Scratch backing: forbidden6 reserves record_capacity, best7/compact13/index arrays
// reserve index_capacity. Failure keeps positions unchanged, discards all scratch.
// Stage 1 encoding, 2 best, 3 dedup, 4 conflicts, 5 commit.
inline Result encode_rank(const std::uint64_t* descriptors,std::uint32_t count,
 const std::uint32_t* owners,std::uint64_t owner_count,
 const std::uint64_t* source_units,std::uint64_t source_unit_count,
 const std::uint32_t* members,std::uint64_t member_count,
 const std::uint64_t* source_trials,std::uint64_t source_trial_count,
 const std::uint64_t* conflicts,const std::uint64_t* sites,std::uint64_t site_count,
 const std::uint32_t* nets,std::uint64_t net_count,
 const std::uint32_t* conflict_units,std::uint64_t conflict_unit_count,
 const std::uint64_t* blocks,std::uint64_t block_count,std::uint64_t* positions,
 std::uint64_t* candidates,std::uint64_t* records,std::uint32_t record_capacity,
 std::uint8_t* kinds,std::uint32_t kind_capacity,
 std::uint64_t* units,std::uint32_t unit_capacity,
 std::uint64_t* trials,std::uint32_t trial_capacity,
 std::uint32_t* order,std::uint32_t* selected,std::uint32_t index_capacity,
 const std::uint64_t* groups,std::uint32_t group_count,
 const std::uint32_t* forbidden_indices,std::uint32_t forbidden_count,
 std::uint64_t* forbidden,std::uint64_t* best7,std::uint64_t* compact13,
 std::uint32_t* group_indices,std::uint32_t* gathered,std::uint32_t* unique_indices){
 if(forbidden_count>record_capacity)return {1,2,0,0};
 for(std::uint32_t i=0;i<forbidden_count;++i)if(forbidden_indices[i]>=count)return {1,1,0,0};
 auto encoded=tileplace_wire_identity_build::encode(descriptors,count,owners,owner_count,source_units,source_unit_count,members,member_count,source_trials,source_trial_count,candidates,record_capacity,kinds,kind_capacity,units,unit_capacity,trials,trial_capacity);
 if(encoded.status)return {1,encoded.status,0,0};
 for(std::uint32_t i=0;i<count;++i){
  for(unsigned j=0;j<7;++j)records[13ULL*i+j]=candidates[7ULL*i+j];
  for(unsigned j=0;j<6;++j)records[13ULL*i+7+j]=conflicts[6ULL*i+j];
 }
 for(std::uint32_t i=0;i<forbidden_count;++i)for(unsigned j=0;j<6;++j)forbidden[6ULL*i+j]=candidates[7ULL*forbidden_indices[i]+1+j];
 auto result=rank_commit(records,count,groups,group_count,forbidden,forbidden_count,kinds,encoded.kinds,units,encoded.units,members,member_count,trials,encoded.trials,sites,site_count,nets,net_count,conflict_units,conflict_unit_count,blocks,block_count,positions,candidates,record_capacity,best7,compact13,group_indices,gathered,unique_indices,order,selected,index_capacity);
 if(result.stage)++result.stage;
 return result;
}
}
