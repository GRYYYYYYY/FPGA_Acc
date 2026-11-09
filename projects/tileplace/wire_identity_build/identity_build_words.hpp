#pragma once
#include "../wire_best/identity_words.hpp"
namespace tileplace_wire_identity_build {
// Five-kind enumerator input, full member identities. All output pools start at zero.
// Member backing is shared with the input units. Validate before any output write.
// Status: 1 kind/count, 2 capacity, 3 unit/member range or order, 4 trial order/ID.
inline void build(unsigned kind,const std::uint32_t* owners,unsigned owner_count,
 const std::uint64_t* units,std::uint64_t unit_count,const std::uint32_t* members,
 std::uint64_t member_count,const std::uint64_t* trial,unsigned trial_count,
 std::uint8_t* kind_output,unsigned kind_capacity,std::uint64_t* unit_output,
 unsigned unit_capacity,std::uint64_t* trial_output,unsigned trial_capacity,
 std::uint64_t* identity_output,unsigned& status){
 status=0;
 if(kind>4||owner_count==0||owner_count>3||trial_count==0){status=1;return;}
 const unsigned lengths[5]={4,4,10,6,6};
 const std::uint8_t names[30]={'m','o','v','e','s','w','a','p','m','a','c','r','o','_','s','w','a','p','c','h','a','i','n','2','c','h','a','i','n','3'};
 const unsigned offsets[5]={0,4,8,18,24};
 if(kind_capacity<lengths[kind]||unit_capacity<owner_count||trial_capacity<trial_count){status=2;return;}
 if(unit_count>UINT64_MAX/4){status=3;return;}
 std::uint32_t sorted[3]={0,0,0};
 for(unsigned i=0;i<owner_count;++i){
  auto id=owners[i];if(id>=unit_count){status=3;return;}
  auto u=units+4ULL*id;auto r=tileplace_wire_best::range(u);
  if(!r.count||!tileplace_hbm::valid_range(r,member_count)){status=3;return;}
  for(std::uint64_t j=1;j<r.count;++j)if(members[r.offset+j-1]>=members[r.offset+j]){status=3;return;}
  for(unsigned j=0;j<i;++j)if(owners[j]==id){status=3;return;}
  sorted[i]=id;
 }
 for(unsigned i=0;i<trial_count;++i)if(trial[3ULL*i]>UINT32_MAX||(i&&trial[3ULL*(i-1)]>=trial[3ULL*i])){status=4;return;}
 // Compare full nested unit members, independent of host unit indices.
 for(unsigned i=1;i<owner_count;++i){
  auto value=sorted[i];unsigned j=i;
  while(j){auto a=tileplace_wire_best::range(units+4ULL*value),b=tileplace_wire_best::range(units+4ULL*sorted[j-1]);
   auto n=a.count<b.count?a.count:b.count;int order=0;
   for(std::uint64_t k=0;k<n;++k){auto x=members[a.offset+k],y=members[b.offset+k];if(x!=y){order=x<y?-1:1;break;}}
   if(!order)order=a.count<b.count?-1:a.count>b.count?1:0;
   if(order>=0)break;
   sorted[j]=sorted[j-1];--j;
  }sorted[j]=value;
 }
 for(unsigned i=0;i<lengths[kind];++i)kind_output[i]=names[offsets[kind]+i];
 for(unsigned i=0;i<owner_count;++i){auto u=units+4ULL*sorted[i];unit_output[2ULL*i]=u[0];unit_output[2ULL*i+1]=u[1];}
 for(unsigned i=0;i<trial_count;++i){trial_output[3ULL*i]=trial[3ULL*i];trial_output[3ULL*i+1]=trial[3ULL*i+1];trial_output[3ULL*i+2]=trial[3ULL*i+2];}
 identity_output[0]=0;identity_output[1]=lengths[kind];identity_output[2]=0;identity_output[3]=owner_count;identity_output[4]=0;identity_output[5]=trial_count;
}
}
