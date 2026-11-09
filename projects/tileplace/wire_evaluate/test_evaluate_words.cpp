#include "evaluate_words.hpp"
#include <iostream>
int main(){std::uint64_t blocks[16]{},positions[4]={0,0,10,0},sites[44]{},moves[3]={2,0,0},guards[2]={2ULL|(5ULL<<32),10},nets[6]={7,0,0,2,0,0};unsigned members[2]={2,5},touched[2];std::int32_t weights[3]={0,0,0};blocks[0]=2;blocks[8]=5;
 for(unsigned i=0;i<11;++i)sites[4*i]=i;
 for(unsigned t=0;t<1000;++t){unsigned x=t%11;moves[1]=x;auto r=tileplace_wire_evaluate::evaluate(blocks,positions,2,sites,11,nullptr,0,moves,1,guards,1,nets,1,members,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,weights,touched,2);
 if(x==10){if(r.stage!=1||r.status||r.accepted)return 1;}else if(r.stage||r.status||r.before[0]!=10||r.after[0]!=10-x||r.score!=-std::int64_t((std::uint64_t(x)*1048576+9)/10)||r.accepted!=unsigned(x>0)||r.touched_count!=1||touched[0]!=7)return 2;
 }
 auto call=[&](unsigned cap){return tileplace_wire_evaluate::evaluate(blocks,positions,2,sites,11,nullptr,0,moves,1,guards,1,nets,1,members,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,weights,touched,cap);};
 moves[1]=3;guards[1]=6;auto r=call(2);if(r.stage!=2||r.status)return 3;guards[1]=10;r=call(0);if(r.stage!=3||r.status!=2)return 4;nets[2]=99;r=call(2);if(r.stage!=3||r.status!=1)return 5;nets[2]=0;weights[0]=-1;r=call(2);if(r.stage!=5||r.status!=1)return 6;
 std::cout<<"1000 composed legality/guard/touched/cost/score cases and stage faults pass\n";
}
