#pragma once
#include "../wire_best/best_words.hpp"
namespace tileplace_wire_dedup {
// Candidate7 records share exact identity pools. Output indices are sorted by identity.
// Duplicate identities retain lowest score, first occurrence on equal score.
// Caller reserves count indices; all validation errors preserve the output.
inline std::uint32_t dedup(const std::uint64_t* candidates,std::uint32_t count,const std::uint8_t* kinds,std::uint64_t kc,const std::uint64_t* units,std::uint64_t uc,const std::uint32_t* members,std::uint64_t mc,const std::uint64_t* trials,std::uint64_t tc,std::uint32_t* output,std::uint32_t capacity,std::uint32_t& status){
 status=0;if(count>capacity){status=2;return 0;}
 tileplace_wire_best::best(candidates,count,nullptr,0,nullptr,0,kinds,kc,units,uc,members,mc,trials,tc,nullptr,0,status);if(status)return 0;
 std::uint32_t size=0;
 for(std::uint32_t i=0;i<count;++i){auto c=candidates+7ULL*i;std::uint32_t j=0;int comparison=1;while(j<size){comparison=tileplace_wire_best::identity(c+1,candidates+7ULL*output[j]+1,kinds,units,members,trials);if(comparison<=0)break;++j;}
 if(j<size&&comparison==0){if(tileplace_wire_best::score(c[0])<tileplace_wire_best::score(candidates[7ULL*output[j]]))output[j]=i;continue;}
 for(auto k=size;k>j;--k){output[k]=output[k-1];}
 output[j]=i;++size;
 }return size;
}
}
