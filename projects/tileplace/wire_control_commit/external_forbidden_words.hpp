#pragma once
#include "../wire_identity_build/batch_words.hpp"
namespace tileplace_wire_control_commit {
struct IdentityPool {
 const std::uint8_t* kinds;std::uint64_t kind_count;
 const std::uint64_t* units;std::uint64_t unit_count;
 const std::uint32_t* members;std::uint64_t member_count;
 const std::uint64_t* trials;std::uint64_t trial_count;
};
struct ExternalForbidden {const std::uint64_t* identities;unsigned count;IdentityPool pool;};
// Full equality across independent pools; offsets are never identity values.
inline bool cross_equal(const std::uint64_t* a,const IdentityPool& x,const std::uint64_t* b,const IdentityPool& y){
 if(a[1]!=b[1]||a[3]!=b[3]||a[5]!=b[5])return false;
 for(std::uint64_t i=0;i<a[1];++i)if(x.kinds[a[0]+i]!=y.kinds[b[0]+i])return false;
 for(std::uint64_t i=0;i<a[3];++i){auto u=x.units+2*(a[2]+i),v=y.units+2*(b[2]+i);if(u[1]!=v[1])return false;
  for(std::uint64_t j=0;j<u[1];++j)if(x.members[u[0]+j]!=y.members[v[0]+j])return false;
 }
 for(std::uint64_t i=0;i<a[5];++i){auto u=x.trials+3*(a[4]+i),v=y.trials+3*(b[4]+i);if(u[0]!=v[0]||u[1]!=v[1]||u[2]!=v[2])return false;}
 return true;
}
// Caller validates backing and canonical complete identities. Range validation
// precedes scored descriptor writes. Candidate scratch may change on error.
inline unsigned filter_external(std::uint64_t* scored,unsigned count,
 const std::uint32_t* owners,std::uint64_t owner_count,
 const std::uint64_t* source_units,unsigned source_unit_count,
 const std::uint32_t* members,std::uint64_t member_count,
 const std::uint64_t* source_trials,std::uint64_t trial_count,
 const ExternalForbidden& blocked,std::uint64_t* candidates,unsigned record_capacity,
 std::uint8_t* kinds,unsigned kind_capacity,std::uint64_t* units,unsigned unit_capacity,
 std::uint64_t* trials,unsigned trial_capacity){
 const auto& p=blocked.pool;unsigned status;
 tileplace_wire_best::best(nullptr,0,nullptr,0,blocked.identities,blocked.count,p.kinds,p.kind_count,p.units,p.unit_count,p.members,p.member_count,p.trials,p.trial_count,nullptr,0,status);
 if(status)return status;
 auto r=tileplace_wire_identity_build::encode(scored,count,owners,owner_count,source_units,source_unit_count,members,member_count,source_trials,trial_count,candidates,record_capacity,kinds,kind_capacity,units,unit_capacity,trials,trial_capacity);
 if(r.status)return r.status;
 IdentityPool local{kinds,r.kinds,units,r.units,members,member_count,trials,r.trials};
 for(unsigned i=0;i<count;++i)for(unsigned j=0;j<blocked.count;++j)if(cross_equal(candidates+7ULL*i+1,local,blocked.identities+6ULL*j,p)){scored[6ULL*i]=0;break;}
 return 0;
}
}
