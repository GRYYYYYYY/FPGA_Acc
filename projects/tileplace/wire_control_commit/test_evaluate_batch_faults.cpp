#include "evaluate_batch_words.hpp"
#include <cassert>
#include <iostream>
int main(){for(unsigned f=0;f<8;++f){
 std::uint64_t blocks[16]={},positions[4]={0,0,10,0},sites[44]={},guards[2]={2ULL|(5ULL<<32),10},nets[6]={7,0,0,2,0,0},descriptors[6]={0,0,0,1,0,1},trials[6]={2,3,0,2,4,0},scored[6]={99},conflicts[6],writes[8];std::uint32_t members[2]={2,5},touched[2],diagnostics[4]={99,99,99,99};std::int32_t weights[3]={0,0,0};blocks[0]=2;blocks[8]=5;for(unsigned i=0;i<11;++i)sites[4*i]=i;
 if(f==1)trials[0]=UINT64_MAX;
 if(f==3)trials[0]=99;
 if(f==5)weights[0]=-1;
 if(f==6)descriptors[5]=2;
 if(f==7)guards[1]=6;
 auto r=tileplace_wire_control_commit::evaluate_batch(blocks,positions,2,sites,11,nullptr,0,guards,1,nets,1,members,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,weights,descriptors,1,trials,2,1,scored,conflicts,f==0?0:1,writes,f==2?0:4,touched,f==4?0:2,diagnostics);
 assert(positions[0]==0&&positions[1]==0&&positions[2]==10&&positions[3]==0);
 if(f==7){assert(!r.stage&&!r.status&&!r.accepted&&scored[0]==0&&diagnostics[0]==2&&diagnostics[1]==0);}
 else{assert(r.stage==(f<2?1:f==2||f==3||f==6?2:3));assert(r.status==(f==0||f==2||f==4?2:f==6?4:1));}
 }std::cout<<"7 batch input/write/evaluator faults + legal guard rejection PASS\n";}
