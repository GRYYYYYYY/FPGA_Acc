#include "batch_words.hpp"
#include "../wire_dedup/dedup_words.hpp"
#include <cassert>
#include <algorithm>
#include <iostream>
#include <map>
#include <random>
#include <string>
#include <tuple>
#include <vector>
static void random_reference(){
 using Id=std::tuple<std::string,std::vector<std::vector<unsigned>>,std::vector<std::tuple<unsigned,long long,long long,long long,long long>>>;
 const std::string names[]={"move","swap","macro_swap","chain2","chain3"};std::mt19937 rng(9713);
 std::uint64_t su[]={0,2,0,0,2,1,0,0,3,2,0,0};std::uint32_t members[]={1,5,9,12,17};
 std::vector<std::vector<unsigned>> full={{1,5},{9},{12,17}};
 for(unsigned run=0;run<1000;++run){
  std::vector<std::uint64_t> input,st;std::vector<std::uint32_t> owners;std::vector<Id> reference;std::vector<long long> scores;
  for(unsigned i=0;i<12;++i){unsigned kind=rng()%5,a=rng()%3,b=(a+1)%3,count=1+rng()%2;long long score=-static_cast<long long>(rng()%8);
   unsigned oo=owners.size(),to=st.size()/3;owners.push_back(a);if(count==2)owners.push_back(b);
   unsigned block=rng()%4;std::uint32_t x=rng()%3,y=0xffffffffU,z=0x80000000U,l=rng()%2;
   st.insert(st.end(),{block,std::uint64_t(x)|(std::uint64_t(y)<<32),std::uint64_t(z)|(std::uint64_t(l)<<32)});
   input.insert(input.end(),{std::uint64_t(score),kind,oo,count,to,1});
   std::vector<std::vector<unsigned>> u={full[a]};if(count==2)u.push_back(full[b]);std::sort(u.begin(),u.end());
   reference.emplace_back(names[kind],u,std::vector<std::tuple<unsigned,long long,long long,long long,long long>>{{block,x,-1,-2147483648LL,l}});scores.push_back(score);
  }
  std::uint64_t records[84],units[72],trials[36];std::uint8_t kinds[120];
  auto r=tileplace_wire_identity_build::encode(input.data(),12,owners.data(),owners.size(),su,3,members,5,st.data(),12,records,12,kinds,120,units,36,trials,12);assert(!r.status);
  std::uint64_t groups[]={0,6,6,6},blocked[6];for(unsigned j=0;j<6;++j)blocked[j]=records[1+j];
  std::uint32_t output[12];unsigned status;tileplace_wire_best::best(records,12,groups,2,blocked,1,kinds,r.kinds,units,r.units,members,5,trials,r.trials,output,12,status);assert(!status);
  for(unsigned g=0;g<2;++g){unsigned chosen=UINT32_MAX;for(unsigned j=g*6;j<g*6+6;++j){if(scores[j]>=0||reference[j]==reference[0])continue;if(chosen==UINT32_MAX||std::tie(scores[j],reference[j])<std::tie(scores[chosen],reference[chosen]))chosen=j;}assert(output[g]==chosen);}
  std::map<Id,unsigned> expected;for(unsigned j=0;j<12;++j){auto p=expected.emplace(reference[j],j);if(!p.second&&scores[j]<scores[p.first->second])p.first->second=j;}
  auto n=tileplace_wire_dedup::dedup(records,12,kinds,r.kinds,units,r.units,members,5,trials,r.trials,output,12,status);assert(!status&&n==expected.size());unsigned j=0;for(const auto& e:expected)assert(output[j++]==e.second);
 }
}
int main(){
 random_reference();
 // Duplicate macro identity with reversed owner ordering, forbidden shared pool,
 // and move/chain tie ordering. Coordinates preserve signed and layer extremes.
 std::uint64_t source_units[]={0,2,0,0,2,1,0,0,3,1,0,0};
 std::uint32_t members[]={2,7,11,19},owners[]={1,0,0,1,2};
 std::uint64_t source_trials[]={2,UINT64_MAX,0x80000000ffffffffULL,7,0,3,11,4,5};
 std::uint64_t input[]={std::uint64_t(-9),2,0,2,0,3,std::uint64_t(-12),2,2,2,0,3,std::uint64_t(-12),0,4,1,2,1,std::uint64_t(-12),3,4,1,2,1};
 std::uint64_t candidates[28],units[24],trials[36];std::uint8_t kinds[40];
 auto r=tileplace_wire_identity_build::encode(input,4,owners,5,source_units,3,members,4,source_trials,3,candidates,4,kinds,40,units,12,trials,12);
 assert(!r.status);assert(tileplace_wire_best::identity(candidates+1,candidates+8,kinds,units,members,trials)==0);
 std::uint64_t groups[]={0,2,2,2},forbidden[6];for(unsigned i=0;i<6;++i)forbidden[i]=candidates[1+i];
 unsigned status;std::uint32_t output[4];auto n=tileplace_wire_best::best(candidates,4,groups,2,forbidden,1,kinds,r.kinds,units,r.units,members,4,trials,r.trials,output,4,status);
 assert(!status&&n==1&&output[0]==UINT32_MAX&&output[1]==3);
 n=tileplace_wire_dedup::dedup(candidates,4,kinds,r.kinds,units,r.units,members,4,trials,r.trials,output,4,status);
 assert(!status&&n==3&&output[0]==3&&output[1]==1&&output[2]==2);
 // Real downstream comparison must see the layer field, including signed minimum.
 auto before=trials[2];trials[11]^=1ULL<<32;
 assert(tileplace_wire_best::identity(candidates+1,candidates+8,kinds,units,members,trials)!=0);trials[11]=before;
 input[2]=6;r=tileplace_wire_identity_build::encode(input,4,owners,5,source_units,3,members,4,source_trials,3,candidates,4,kinds,40,units,12,trials,12);assert(r.status==3);
 std::cout<<"1000 independent tuple references + batch identity -> forbidden best / stable dedup composition PASS\n";
}
