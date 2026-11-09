#include "encode_rank_words.hpp"
#include <cassert>
#include <iostream>
int main(){
 for(unsigned kind=0;kind<5;++kind)for(unsigned mode=0;mode<6;++mode){
  std::uint64_t descriptors[12]={std::uint64_t(-5),kind,0,1,0,1,std::uint64_t(-7),kind,1,1,1,1};
  std::uint32_t owners[2]={0,1},members[2]={1,2},nets[2]={3,mode==1?3U:4U},conflict_units[2]={0,1},order[2],selected[2];
  std::uint64_t source_units[8]={0,1,0,0,1,1,0,0},source_trials[6]={1,UINT64_MAX,0x8000000000000000ULL,2,7,8},blocks[16]={1},positions[4]={11,22,33,44};blocks[8]=2;
  std::uint64_t conflicts[12]={0,0,0,1,0,1,0,0,1,1,1,1},candidates[14],records[26],units[8],trials[6];std::uint8_t kinds[20];
  if(mode==2)descriptors[1]=5;
  if(mode==3)conflicts[8]=3;
  if(mode==4)source_trials[3]=1;
  std::uint64_t groups[4]={0,1,1,1},forbidden[12],best7[14],compact13[26];std::uint32_t fi[1]={0},gi[2],gathered[2],unique[2];
  auto r=tileplace_wire_control_commit::encode_rank(descriptors,2,owners,2,source_units,2,members,2,source_trials,2,conflicts,nullptr,0,nets,2,conflict_units,2,blocks,2,positions,candidates,records,2,kinds,20,units,4,trials,2,order,selected,2,groups,2,fi,mode==5?1:0,forbidden,best7,compact13,gi,gathered,unique);
  if(mode>=2&&mode<5){assert(r.stage==(mode==2?1:mode==3?4:5)&&r.status==(mode==2?1:mode==3?1:3));assert(positions[0]==11&&positions[1]==22&&positions[2]==33&&positions[3]==44);}
  else if(mode==5){assert(!r.status&&r.selected==1&&selected[0]==1&&positions[0]==11&&positions[1]==22&&positions[2]==7&&positions[3]==8);}
  else{assert(!r.stage&&!r.status&&r.selected==(mode?1U:2U)&&r.moved==r.selected);assert(selected[0]==1&&positions[2]==7&&positions[3]==8);assert(positions[0]==(mode?11:UINT64_MAX)&&positions[1]==(mode?22:0x8000000000000000ULL));}
 }
 std::cout<<"30 encode -> best -> dedup -> conflicts -> commit cases PASS\n";
}
