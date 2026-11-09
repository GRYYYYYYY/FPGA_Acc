#pragma once
#include <cstdint>
namespace tileplace_cost_array {
struct ScoreResult {std::int64_t score;std::uint32_t status,reserved;};
inline bool normalized(std::uint64_t before,std::uint64_t after,std::int64_t& result){
 __int128 numerator=(__int128(after)-__int128(before))*1048576;
 __int128 denominator=before?before:1;
 auto quotient=numerator/denominator;
 if(numerator%denominator<0)--quotient;
 if(quotient<INT64_MIN||quotient>INT64_MAX)return false;
 result=std::int64_t(quotient);return true;
}
// Status 1: negative weight; 2: individual delta overflow; 3: total overflow.
inline ScoreResult score_array(const std::uint64_t before[4],const std::uint64_t after[4],const std::int32_t weights[3]){
 ScoreResult out{};std::int64_t delta;
 if(!normalized(before[0],after[0],delta)){out.status=2;return out;}
 __int128 total=delta;
 for(unsigned i=1;i<4;++i){
  if(weights[i-1]<0){out.status=1;return out;}
  if(!normalized(before[i],after[i],delta)){out.status=2;return out;}
  total+=__int128(weights[i-1])*delta;
 }
 if(total<INT64_MIN||total>INT64_MAX){out.status=3;return out;}
 out.score=std::int64_t(total);return out;
}
}
