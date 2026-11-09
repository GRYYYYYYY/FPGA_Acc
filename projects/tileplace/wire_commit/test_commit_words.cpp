#include "commit_words.hpp"
#include "../wire_transactions/selection_words.hpp"
#include <algorithm>
#include <cassert>
#include <iostream>
#include <map>
#include <random>
#include <vector>
int main(){
 // Actual word selection -> atomic word commit, with shared-net rejection.
 for(unsigned conflict=0;conflict<2;++conflict){
  std::uint64_t blocks[16]={1},positions[4]={0,0,0,0},trial[6]={1,UINT64_MAX,0x8000000000000000ULL,2,7,8};blocks[8]=2;
  std::uint8_t kinds[4]={'m','o','v','e'};std::uint64_t units[4]={0,1,1,1};std::uint32_t members[2]={1,2},nets[2]={3,conflict?3U:4U},owners[2]={0,1};
  std::uint64_t records[26]={std::uint64_t(-5),0,4,0,1,0,1,0,0,0,1,0,1,std::uint64_t(-7),0,4,1,1,1,1,0,0,1,1,1,1};
  std::uint32_t order[2],selected[2];unsigned status;
  auto n=tileplace_wire_transactions::select(records,2,kinds,4,units,2,members,2,trial,2,nullptr,0,nets,2,owners,2,order,2,selected,2,status);
  assert(!status&&n==(conflict?1U:2U)&&selected[0]==1);
  auto moved=tileplace_wire_commit::commit(records,2,selected,n,trial,2,blocks,2,positions,status);assert(!status&&moved==n);
  assert(positions[2]==7&&positions[3]==8);assert(positions[0]==(conflict?0:UINT64_MAX));assert(positions[1]==(conflict?0:0x8000000000000000ULL));
 }
 std::mt19937_64 rng(6131);
 for(unsigned run=0;run<3000;++run){
  std::vector<std::uint64_t> blocks(8*20),positions(2*20),trials,records(13*4);std::map<unsigned,std::pair<std::uint64_t,std::uint64_t>> reference;
  for(unsigned i=0;i<20;++i){blocks[8*i]=i*3+1;positions[2*i]=rng();positions[2*i+1]=rng();reference[i*3+1]={positions[2*i],positions[2*i+1]};}
  std::vector<unsigned> ids;for(unsigned i=0;i<20;++i)ids.push_back(i*3+1);std::shuffle(ids.begin(),ids.end(),rng);
  unsigned next=0;for(unsigned i=0;i<4;++i){auto n=rng()%5;records[13*i+5]=trials.size()/3;records[13*i+6]=n;for(unsigned j=0;j<n;++j){auto id=ids[next++];trials.insert(trials.end(),{id,rng(),rng()});}}
  std::uint32_t selected[4];unsigned sc=0;std::uint64_t expected=0;
  for(unsigned i=0;i<4;++i)if(rng()%2){selected[sc++]=i;for(unsigned j=0;j<records[13*i+6];++j){auto t=trials.data()+3*(records[13*i+5]+j);reference[t[0]]={t[1],t[2]};++expected;}}
  unsigned status;auto moved=tileplace_wire_commit::commit(records.data(),4,selected,sc,trials.data(),trials.size()/3,blocks.data(),20,positions.data(),status);assert(!status&&moved==expected);
  for(unsigned i=0;i<20;++i){assert(positions[2*i]==reference[i*3+1].first);assert(positions[2*i+1]==reference[i*3+1].second);}
 }
 for(unsigned f=0;f<5;++f){std::uint64_t blocks[16]={1},positions[4]={11,22,33,44},trials[6]={1,5,6,2,7,8},records[26]={};blocks[8]=2;records[6]=1;records[18]=1;records[19]=1;std::uint32_t selected[2]={0,1};unsigned status;
  if(f==0)selected[1]=2;
  if(f==1)records[18]=3;
  if(f==2)trials[3]=9;
  if(f==3)trials[3]=1;
  auto n=tileplace_wire_commit::commit(records,2,selected,2,trials,f==4?UINT64_MAX:2,blocks,2,positions,status);assert(!n&&status==(f<2?1:f==2?2:f==3?3:4));assert(positions[0]==11&&positions[1]==22&&positions[2]==33&&positions[3]==44);
 }
 std::cout<<"3000 independent map commits + 5 whole-batch atomic faults PASS\n";
}
