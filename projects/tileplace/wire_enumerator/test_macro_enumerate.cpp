#include "enumerate_words.hpp"
#include <iostream>
int main(){std::uint64_t units[8]={0,2,0,0,2,2,0,0},blocks[32]{},positions[8]={0,0,1,0,4,0,5,0},sites[32]{},roots[16],chain_roots[16],first[12],second[12],merged[12];unsigned members[4]={2,5,8,11};for(unsigned i=0;i<4;++i){blocks[8*i]=members[i];blocks[8*i+7]=std::uint64_t(i/2)<<32;}for(unsigned i=0;i<8;++i)sites[4*i]=i;unsigned status,macros=0;
 auto emit=[&](unsigned kind,const unsigned* moved,unsigned groups,const std::uint64_t* trial,unsigned count){if(kind!=2)return;++macros;if(groups!=2||moved[0]!=0||moved[1]!=1||count!=4)throw 1;unsigned ids[4]={2,5,8,11},xs[4]={4,5,0,1};for(unsigned i=0;i<4;++i)if(trial[3*i]!=ids[i]||trial[3*i+1]!=xs[i]||trial[3*i+2])throw 2;};
 tileplace_wire_enumerator::enumerate(0,units,2,members,blocks,positions,4,sites,8,8,8,8,8,roots,8,chain_roots,8,first,second,merged,4,emit,status);if(status||!macros)return 1;
 units[6]=1;macros=0;tileplace_wire_enumerator::enumerate(0,units,2,members,blocks,positions,4,sites,8,8,8,8,8,roots,8,chain_roots,8,first,second,merged,4,emit,status);if(status||macros)return 2;
 std::cout<<"macro swap exact four-block trials and fixed-other suppression pass\n";}
