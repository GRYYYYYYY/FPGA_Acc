#ifdef NDEBUG
#undef NDEBUG
#endif
#include "search_cost.hpp"
#include <cassert>
#include <random>
int main(){
 std::mt19937_64 rng(731);
 for(unsigned i=0;i<100000;++i){
  uint64_t hi=rng(),lo=rng(),weight=rng(),otherhi=rng(),otherlo=rng();
  routecast::SearchCost a(hi,lo),b(otherhi,otherlo);unsigned __int128 native=(static_cast<unsigned __int128>(hi)<<64)|lo;unsigned __int128 other=(static_cast<unsigned __int128>(otherhi)<<64)|otherlo;
  auto sum=a+weight;auto expected=native+weight;
  assert(sum.low==uint64_t(expected)&&sum.high==uint64_t(expected>>64));assert((a<b)==(native<other));assert((a==b)==(native==other));assert((a!=b)==(native!=other));
 }
 auto carry=routecast::SearchCost(UINT64_MAX)+uint64_t(1);assert(carry.high==1&&carry.low==0);
 assert(routecast::SearchCost(0)==0);assert(routecast::SearchCost(1)<routecast::SearchCost(1,0));
}
