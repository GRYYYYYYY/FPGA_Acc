#include "evaluate_batch_words.hpp"
#include <cassert>
#include <iostream>
int main(){
 std::uint64_t blocks[16]={},positions[4]={0,0,10,0},sites[44]={},guards[2]={2ULL|(5ULL<<32),10},nets[6]={7,0,0,2,0,0};std::uint32_t members[2]={2,5};std::int32_t weights[3]={0,0,0};blocks[0]=2;blocks[8]=5;
 for(unsigned i=0;i<11;++i)sites[4*i]=i;
 for(unsigned i=0;i<1000;++i){unsigned x=i%11;std::uint64_t descriptors[12]={99,0,0,1,0,1,99,0,0,1,1,1},trials[6]={2,x,0,2,0,0},scored[12],conflicts[12],writes[8];std::uint32_t touched[2],diagnostics[8];
 auto r=tileplace_wire_control_commit::evaluate_batch(blocks,positions,2,sites,11,nullptr,0,guards,1,nets,1,members,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,weights,descriptors,2,trials,2,1,scored,conflicts,2,writes,4,touched,2,diagnostics);
 assert(!r.stage&&!r.status&&positions[0]==0&&positions[2]==10);assert(scored[6]==0&&diagnostics[6]==0);assert(r.accepted==unsigned(x>0&&x<10));
 if(x>0&&x<10){auto score=-std::int64_t((std::uint64_t(x)*1048576+9)/10);assert(scored[0]==std::uint64_t(score)&&r.touched==1&&touched[0]==7&&conflicts[3]==1);}else assert(scored[0]==0);
 }
 std::cout<<"1000 analytic evaluated batches: accepted, unchanged, occupied rejection PASS\n";
}
