#pragma once
#include <cstdint>
namespace routecast {
// Two fixed-width words, independent of compiler-native 128-bit support.
// Search simple-path bound guarantees accumulated sums stay below 2^128.
struct SearchCost {
 uint64_t high,low;
 constexpr SearchCost(uint64_t value=0):high(0),low(value){}
 constexpr SearchCost(uint64_t hi,uint64_t lo):high(hi),low(lo){}
 SearchCost operator+(uint64_t value) const {uint64_t next=low+value;return SearchCost(high+(next<low),next);}
 bool operator<(const SearchCost& other)const{return high<other.high||(high==other.high&&low<other.low);}
 bool operator==(const SearchCost& other)const{return high==other.high&&low==other.low;}
 bool operator!=(const SearchCost& other)const{return !(*this==other);}
};
}
