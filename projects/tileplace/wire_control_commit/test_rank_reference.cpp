#include "rank_commit_words.hpp"
#include <algorithm>
#include <cassert>
#include <iostream>
#include <map>
#include <random>
#include <set>
#include <string>
#include <tuple>
#include <vector>
int main(){
 using Id=std::tuple<std::string,unsigned,unsigned>;
 const std::string names[5]={"move","swap","macro_swap","chain2","chain3"};
 std::mt19937 rng(7813);
 for(unsigned run=0;run<2000;++run){
  std::vector<std::uint8_t> kinds;std::uint64_t kind_offsets[5];
  for(unsigned k=0;k<5;++k){kind_offsets[k]=kinds.size();kinds.insert(kinds.end(),names[k].begin(),names[k].end());}
  std::uint64_t units[8]={0,1,1,1,2,1,3,1},trials[24],blocks[32]={},positions[8]={},records[156]={};
  std::uint32_t members[4]={1,2,3,4},nets[8],conflict_units[8];Id archetypes[8];
  for(unsigned a=0;a<8;++a){unsigned block=a%4;archetypes[a]={names[a%5],block+1,a+1};trials[3*a]=block+1;trials[3*a+1]=a+1;trials[3*a+2]=0;nets[a]=rng()%4;conflict_units[a]=block;}
  for(unsigned b=0;b<4;++b)blocks[8*b]=b+1;
  unsigned source[12];long long scores[12];
  for(unsigned i=0;i<12;++i){auto a=rng()%8;source[i]=a;scores[i]=-static_cast<long long>(rng()%8);auto r=records+13*i;r[0]=std::uint64_t(scores[i]);r[1]=kind_offsets[a%5];r[2]=names[a%5].size();r[3]=a%4;r[4]=1;r[5]=a;r[6]=1;r[9]=a;r[10]=1;r[11]=a;r[12]=1;}
  bool blocked=run%2;Id forbidden_id=archetypes[source[0]];std::uint64_t forbidden[6];for(unsigned j=0;j<6;++j)forbidden[j]=records[1+j];
  std::map<Id,unsigned> unique;
  for(unsigned g=0;g<3;++g){unsigned best=UINT32_MAX;
   for(unsigned i=g*4;i<g*4+4;++i){const auto& id=archetypes[source[i]];if(scores[i]>=0||(blocked&&id==forbidden_id))continue;
    if(best==UINT32_MAX||std::tie(scores[i],id)<std::tie(scores[best],archetypes[source[best]]))best=i;
   }
   if(best!=UINT32_MAX){auto e=unique.emplace(archetypes[source[best]],best);if(!e.second&&scores[best]<scores[e.first->second])e.first->second=best;}
  }
  std::vector<unsigned> sorted;for(const auto& e:unique)sorted.push_back(e.second);
  std::sort(sorted.begin(),sorted.end(),[&](unsigned a,unsigned b){return std::tie(scores[a],archetypes[source[a]])<std::tie(scores[b],archetypes[source[b]]);});
  std::vector<unsigned> expected;std::set<unsigned> used_units,used_nets;std::uint64_t expected_positions[8]={};
  for(auto i:sorted){auto a=source[i],u=conflict_units[a],n=nets[a];if(used_units.count(u)||used_nets.count(n))continue;used_units.insert(u);used_nets.insert(n);expected.push_back(i);expected_positions[2*u]=a+1;}
  std::uint64_t groups[6]={0,4,4,4,8,4},candidates[84],best7[21],compact13[39];std::uint32_t gi[3],gathered[3],indices[3],order[3],selected[3];
  auto result=tileplace_wire_control_commit::rank_commit(records,12,groups,3,forbidden,blocked?1:0,kinds.data(),kinds.size(),units,4,members,4,trials,8,nullptr,0,nets,8,conflict_units,8,blocks,4,positions,candidates,12,best7,compact13,gi,gathered,indices,order,selected,3);
  assert(!result.stage&&!result.status&&result.selected==expected.size()&&result.moved==expected.size()&&result.proposals==unique.size());
  for(unsigned i=0;i<expected.size();++i)assert(selected[i]==expected[i]);
  for(unsigned i=0;i<8;++i)assert(positions[i]==expected_positions[i]);
 }
 std::cout<<"2000 independent tuple/map/set rank-selection-commit references PASS\n";
}
