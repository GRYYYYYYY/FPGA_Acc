#pragma once
#include "../wire_identity_build/batch_words.hpp"
#include "../wire_transactions/selection_words.hpp"
#include "../wire_commit/commit_words.hpp"
namespace tileplace_wire_control_commit {
struct Result {unsigned stage,status,selected;std::uint64_t moved;unsigned proposals=0;};
// Compose identity construction, conflict selection and atomic position commit.
// Caller supplies scored, per-unit-best, deduplicated candidates and conflict
// metadata6 (site/net/unit ranges). Scratch is discardable on failure; positions
// change only after complete validation. No enumeration/evaluation/feedback here.
inline Result run(const std::uint64_t* descriptors,std::uint32_t count,
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
 std::uint32_t* order,std::uint32_t* selected,std::uint32_t index_capacity){
 auto encoded=tileplace_wire_identity_build::encode(descriptors,count,owners,owner_count,source_units,source_unit_count,members,member_count,source_trials,source_trial_count,candidates,record_capacity,kinds,kind_capacity,units,unit_capacity,trials,trial_capacity);
 if(encoded.status)return {1,encoded.status,0,0};
 for(std::uint32_t i=0;i<count;++i){
  for(unsigned j=0;j<7;++j)records[13ULL*i+j]=candidates[7ULL*i+j];
  for(unsigned j=0;j<6;++j)records[13ULL*i+7+j]=conflicts[6ULL*i+j];
 }
 unsigned status;
 auto n=tileplace_wire_transactions::select(records,count,kinds,encoded.kinds,units,encoded.units,members,member_count,trials,encoded.trials,sites,site_count,nets,net_count,conflict_units,conflict_unit_count,order,index_capacity,selected,index_capacity,status);
 if(status)return {2,status,0,0};
 auto moved=tileplace_wire_commit::commit(records,count,selected,n,trials,encoded.trials,blocks,block_count,positions,status);
 if(status)return {3,status,0,0};
 return {0,0,n,moved};
}
}
