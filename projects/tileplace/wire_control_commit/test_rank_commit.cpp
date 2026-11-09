#include "rank_commit_words.hpp"
#include <cassert>
#include <iostream>
int main(){
 for(unsigned mode=0;mode<6;++mode){
  std::uint64_t records[52]={},groups[6]={0,2,2,1,3,1},units[4]={0,1,1,1},trials[6]={1,5,6,2,7,8},blocks[16]={1},positions[4]={11,22,33,44},forbidden[6]={0,4,0,1,0,1};blocks[8]=2;
  std::uint8_t kinds[4]={'m','o','v','e'};std::uint32_t members[2]={1,2},owners[2]={0,1},nets[2]={3,mode==2?3U:4U};
  for(unsigned i=0;i<4;++i){auto r=records+13*i;bool second=i==3;r[0]=std::uint64_t(i==0?-3:i==1?-9:i==2?-7:-8);r[2]=4;r[3]=second?1:0;r[4]=1;r[5]=second?1:0;r[6]=1;r[9]=second?1:0;r[10]=1;r[11]=second?1:0;r[12]=1;}
  if(mode==3)groups[1]=5;
  if(mode==4)records[13+9]=3;
  if(mode==5)trials[3]=1;
  std::uint64_t candidates[28],best[21],compact[39];std::uint32_t gi[3],gathered[3],unique[3],order[3],selected[3];
  auto r=tileplace_wire_control_commit::rank_commit(records,4,groups,3,forbidden,mode==1?1:0,kinds,4,units,2,members,2,trials,2,nullptr,0,nets,2,owners,2,blocks,2,positions,candidates,4,best,compact,gi,gathered,unique,order,selected,3);
  if(mode>=3){assert(r.stage==(mode==3?1:mode==4?3:4));assert(positions[0]==11&&positions[1]==22&&positions[2]==33&&positions[3]==44);}
  else if(mode==1){assert(!r.status&&r.selected==1&&selected[0]==3&&positions[0]==11&&positions[2]==7);}
  else if(mode==2){assert(!r.status&&r.selected==1&&selected[0]==1&&positions[0]==5&&positions[2]==33);}
  else{assert(!r.status&&r.selected==2&&selected[0]==1&&selected[1]==3&&positions[0]==5&&positions[2]==7);}
 }
 std::cout<<"best/forbidden -> stable dedup -> conflict select -> atomic commit PASS\n";
}
