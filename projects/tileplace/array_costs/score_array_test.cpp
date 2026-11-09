#include "score_array.hpp"
#include "../cpp_snapshot/score.hpp"
#include <random>
#include <iostream>
int main(){
 std::mt19937_64 rng(39);unsigned passed=0,rejected=0;
 for(unsigned test=0;test<5000;++test){tileplace_snapshot::Cost before,after;std::array<std::int32_t,3> weights;
  for(unsigned i=0;i<4;++i){before[i]=rng();after[i]=rng();if(test%17==0)before[i]=0;}
  for(unsigned i=0;i<3;++i)weights[i]=test%19==0?-1:std::int32_t(rng()%100);
  auto actual=tileplace_cost_array::score_array(before.data(),after.data(),weights.data());
  try{auto expected=tileplace_snapshot::transaction_score(before,after,weights);if(actual.status||actual.reserved||actual.score!=expected)return 1;++passed;}
  catch(const std::invalid_argument&){if(actual.status!=1||actual.score||actual.reserved)return 2;++rejected;}
  catch(const std::overflow_error&){if((actual.status!=2&&actual.status!=3)||actual.score||actual.reserved)return 3;++rejected;}
 }
 std::uint64_t before[4]={3,1,1,1},after[4]={2,1,1,1};std::int32_t weights[3]={1,1,1};
 auto actual=tileplace_cost_array::score_array(before,after,weights);if(actual.status||actual.score!=-349526)return 4;
 before[0]=0;after[0]=UINT64_MAX;if(tileplace_cost_array::score_array(before,after,weights).status!=2)return 5;
 before[0]=after[0]=1;after[1]=1000000000000ULL;weights[0]=INT32_MAX;if(tileplace_cost_array::score_array(before,after,weights).status!=3)return 6;
 after[1]=1;weights[0]=-1;if(tileplace_cost_array::score_array(before,after,weights).status!=1)return 7;
 std::cout<<"5000 scores: "<<passed<<" valid, "<<rejected<<" errors; floor and 3 status checks pass\n";
}
