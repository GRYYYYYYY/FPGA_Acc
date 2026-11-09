#pragma once
#include "net_cost.hpp"

namespace tileplace_snapshot {
inline std::int64_t narrow_score(__int128 value) {
    if(value<INT64_MIN || value>INT64_MAX) throw std::overflow_error("transaction score exceeds int64");
    return std::int64_t(value);
}
inline std::int64_t normalized_delta(std::uint64_t before,std::uint64_t after) {
    // Python // rounds toward negative infinity, unlike C++ integer division.
    __int128 numerator=(__int128(after)-__int128(before))*1048576;
    __int128 denominator=std::max<std::uint64_t>(1,before);
    auto quotient=numerator/denominator;
    if(numerator%denominator<0) --quotient;
    return narrow_score(quotient);
}
inline std::int64_t transaction_score(const Cost& before,const Cost& after,
                                      std::array<std::int32_t,3> weights) {
    __int128 result=normalized_delta(before[0],after[0]);
    for(unsigned i=1;i<4;++i) {
        if(weights[i-1]<0) throw std::invalid_argument("negative score weight");
        result+=__int128(weights[i-1])*normalized_delta(before[i],after[i]);
    }
    return narrow_score(result);
}
}
