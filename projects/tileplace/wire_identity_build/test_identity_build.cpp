#include "identity_build_words.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <iostream>
#include <random>
#include <string>
#include <vector>
int main(){
 std::mt19937 rng(8317);const std::string names[5]={"move","swap","macro_swap","chain2","chain3"};
 for(unsigned run=0;run<3000;++run){
  std::vector<std::uint32_t> members;std::vector<std::uint64_t> units;
  std::vector<std::vector<std::uint32_t>> reference;
  for(unsigned i=0;i<6;++i){std::vector<std::uint32_t> m;unsigned n=1+rng()%5;for(unsigned j=0;j<n;++j)m.push_back(i*20+j*2);units.insert(units.end(),{members.size(),n,0,0});members.insert(members.end(),m.begin(),m.end());reference.push_back(m);}
  std::array<std::uint32_t,6> indices={0,1,2,3,4,5};std::shuffle(indices.begin(),indices.end(),rng);
  unsigned count=1+rng()%3,kind=run%5;std::vector<std::vector<std::uint32_t>> expected;
  for(unsigned i=0;i<count;++i)expected.push_back(reference[indices[i]]);
  std::sort(expected.begin(),expected.end());
  std::uint64_t trial[9]={1,rng(),rng(),7,rng(),rng(),19,rng(),rng()},out_trial[9],out_units[6],identity[6];std::uint8_t text[10];unsigned status;
  tileplace_wire_identity_build::build(kind,indices.data(),count,units.data(),6,members.data(),members.size(),trial,3,text,10,out_units,3,out_trial,3,identity,status);
  assert(status==0);assert(std::string(text,text+identity[1])==names[kind]);assert(identity[3]==count&&identity[5]==3);
  for(unsigned i=0;i<count;++i){auto start=out_units[2*i],n=out_units[2*i+1];assert(std::vector<std::uint32_t>(members.begin()+start,members.begin()+start+n)==expected[i]);}
  assert(std::equal(trial,trial+9,out_trial));
 }
 // Every status rejects atomically, including invalid full member ordering.
 for(unsigned fault=0;fault<7;++fault){
  std::uint32_t owners[2]={0,1},members[3]={1,3,8};std::uint64_t units[8]={0,2,0,0,2,1,0,0},trial[6]={1,UINT64_MAX,UINT64_MAX,8,0,0};
  std::array<std::uint8_t,10> text;text.fill(77);std::array<std::uint64_t,6> u,t,id;u.fill(77);t.fill(77);id.fill(77);unsigned status;
  if(fault==2)owners[1]=0;
  if(fault==3)units[4]=4;
  if(fault==4)members[1]=0;
  if(fault==5)trial[3]=1;
  if(fault==6)trial[0]=UINT64_MAX;
  tileplace_wire_identity_build::build(fault==0?5:0,owners,2,units,2,members,3,trial,2,text.data(),fault==1?0:10,u.data(),3,t.data(),2,id.data(),status);
  assert(status==(fault==0?1:fault==1?2:fault<5?3:4));
  for(auto x:text)assert(x==77);
  for(auto x:u)assert(x==77);
  for(auto x:t)assert(x==77);
  for(auto x:id)assert(x==77);
 }
 std::cout<<"3000 full identity references and 7 atomic faults PASS\n";
}
