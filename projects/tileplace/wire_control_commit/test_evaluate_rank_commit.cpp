#include "evaluate_batch_words.hpp"
#include "encode_rank_words.hpp"
#include <cassert>
#include <iostream>
int main(){
 std::uint64_t blocks[16]={},positions[4]={0,0,10,0},sites[44]={},guards[2]={2ULL|(5ULL<<32),10},nets[6]={7,0,0,2,0,0};std::uint32_t members[2]={2,5};std::int32_t weights[3]={0,0,0};blocks[0]=2;blocks[8]=5;
 for(unsigned i=0;i<11;++i)sites[4*i]=i;
 for(unsigned i=0;i<1000;++i){unsigned x=i%11;std::uint64_t descriptors[12]={99,0,0,1,0,1,99,0,0,1,1,1},trials[6]={2,x,0,2,0,0},scored[12],conflicts[12],writes[8];std::uint32_t touched[2],diagnostics[8];
 auto r=tileplace_wire_control_commit::evaluate_batch(blocks,positions,2,sites,11,nullptr,0,guards,1,nets,1,members,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,weights,descriptors,2,trials,2,1,scored,conflicts,2,writes,4,touched,2,diagnostics);
 assert(!r.stage&&!r.status&&positions[0]==0&&positions[2]==10);assert(scored[6]==0&&diagnostics[6]==0);assert(r.accepted==unsigned(x>0&&x<10));
 if(x>0&&x<10){auto score=-std::int64_t((std::uint64_t(x)*1048576+9)/10);assert(scored[0]==std::uint64_t(score)&&r.touched==1&&touched[0]==7&&conflicts[3]==1);}else assert(scored[0]==0);
 std::uint64_t identity_source_units[4]={0,1,0,0},groups[2]={0,2},candidates[14],records[26],identity_units[8],identity_trials[6],forbidden[12],best7[14],compact13[26];std::uint8_t kinds[20];
 std::uint32_t identity_members[1]={2},owners[1]={0},order[2],selected[2],fi[1]={0},gi[2],gathered[2],unique[2];
 bool blocked=i%2;
 auto committed=tileplace_wire_control_commit::encode_rank(scored,2,owners,1,identity_source_units,1,identity_members,1,trials,2,conflicts,writes,r.writes,touched,r.touched,owners,1,blocks,2,positions,candidates,records,2,kinds,20,identity_units,4,identity_trials,2,order,selected,2,groups,1,fi,blocked?1:0,forbidden,best7,compact13,gi,gathered,unique);
 bool accept=x>0&&x<10&&!blocked;
 assert(!committed.stage&&!committed.status&&committed.selected==unsigned(accept)&&committed.moved==unsigned(accept));
 if(accept)assert(selected[0]==0);
 assert(positions[0]==(accept?x:0)&&positions[1]==0&&positions[2]==10&&positions[3]==0);
 positions[0]=0;

 }
 std::cout<<"1000 analytic evaluate -> identity -> forbidden/best/dedup/conflicts -> commit batches PASS\n";
}
