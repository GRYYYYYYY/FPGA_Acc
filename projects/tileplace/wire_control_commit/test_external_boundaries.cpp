#include "external_forbidden_words.hpp"
#include <cassert>
#include <iostream>
int main(){
 // Same identity, different offsets in each external pool. Preserve signed
 // extrema in x/y/subtile/layer; offsets are not compared as identity values.
 for(unsigned test=0;test<12;++test){
  std::uint64_t scored[6]={std::uint64_t(-9),0,0,1,0,1},source_units[4]={0,2,0,0},source_trials[3]={7,0x80000000ffffffffULL,0x7fffffff80000000ULL};
  std::uint32_t owners[1]={0},members[2]={7,19};
  std::uint8_t ext_kinds[5]={'!','m','o','v','e'},kinds[10];
  std::uint64_t ext_units[4]={0,0,1,2},ext_trials[6]={0,0,0,7,source_trials[1],source_trials[2]},identity[6]={1,4,1,1,1,1},candidates[7],units[6],trials[3];
  std::uint32_t ext_members[3]={99,7,19};
  if(test>=1&&test<=4){unsigned axis=test-1;ext_trials[4+axis/2]^=1ULL<<((axis%2)*32);}
  if(test==5)ext_members[2]=20;
  if(test==6)ext_kinds[4]='x';
  if(test==7)identity[0]=9;
  if(test==8)ext_units[2]=9;
  if(test==9)identity[4]=9;
  if(test==10)source_trials[0]=UINT64_MAX;
  tileplace_wire_control_commit::ExternalForbidden blocked{identity,1,{ext_kinds,5,ext_units,2,ext_members,3,ext_trials,test==11?UINT64_MAX:2}};
  auto status=tileplace_wire_control_commit::filter_external(scored,1,owners,1,source_units,1,members,2,source_trials,1,blocked,candidates,1,kinds,10,units,3,trials,1);
  if(test>=7){assert(status!=0&&scored[0]==std::uint64_t(-9));}
  else{assert(!status&&scored[0]==(test==0?0:std::uint64_t(-9)));}
 }
 std::cout<<"12 independent-pool equality, four-axis sensitivity and range/ID/scaling faults PASS\n";
}
