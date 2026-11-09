#pragma once
#include "identity_build_words.hpp"
#include "../wire_best/best_words.hpp"
namespace tileplace_wire_identity_build {
struct BatchResult {std::uint64_t kinds,units,trials;unsigned status;};
// Input6: signed score bits, kind, owner offset/count, trial offset/count.
// Output7 candidates share exact pools. On failure discard the complete batch:
// scratch can contain earlier records. Array backing/aliasing is host validated.
inline BatchResult encode(const std::uint64_t* input,std::uint32_t count,
 const std::uint32_t* owners,std::uint64_t owner_count,
 const std::uint64_t* source_units,std::uint64_t source_unit_count,
 const std::uint32_t* members,std::uint64_t member_count,
 const std::uint64_t* source_trials,std::uint64_t source_trial_count,
 std::uint64_t* candidates,std::uint32_t candidate_capacity,
 std::uint8_t* kinds,std::uint32_t kind_capacity,
 std::uint64_t* units,std::uint32_t unit_capacity,
 std::uint64_t* trials,std::uint32_t trial_capacity){
 BatchResult out{};
 if(count>candidate_capacity){out.status=2;return out;}
 if(source_trial_count>UINT64_MAX/3){out.status=4;return out;}
 for(std::uint32_t i=0;i<count;++i){auto d=input+6ULL*i;
  if(d[1]>4||d[3]==0||d[3]>3||d[5]==0||d[5]>UINT32_MAX){out.status=1;return out;}
  if(!tileplace_hbm::valid_range({d[2],d[3]},owner_count)){out.status=3;return out;}
  if(!tileplace_hbm::valid_range({d[4],d[5]},source_trial_count)){out.status=4;return out;}
 }
 for(std::uint32_t i=0;i<count;++i){auto d=input+6ULL*i;std::uint64_t id[6];unsigned status;
  build(unsigned(d[1]),owners+d[2],unsigned(d[3]),source_units,source_unit_count,members,member_count,
   source_trials+3*d[4],unsigned(d[5]),kinds+out.kinds,kind_capacity-unsigned(out.kinds),
   units+2*out.units,unit_capacity-unsigned(out.units),trials+3*out.trials,
   trial_capacity-unsigned(out.trials),id,status);
  if(status){out.status=status;return out;}
  auto c=candidates+7ULL*i;c[0]=d[0];c[1]=out.kinds;c[2]=id[1];c[3]=out.units;c[4]=id[3];c[5]=out.trials;c[6]=id[5];
  out.kinds+=id[1];out.units+=id[3];out.trials+=id[5];
 }
 return out;
}
}
