#include "enumerate_descriptors.hpp"
#include <cassert>
#include <iostream>
int main(){
 std::uint64_t units[8]={0,3,0,0,3,3,0,0},blocks[48]={},positions[12]={0,0,1,0,2,0,5,0,6,0,7,0},sites[40]={},roots[20],chain_roots[20],first[18],second[18],merged[18],descriptors[768],trials[2304];std::uint32_t members[6]={2,5,8,11,14,17},owners[384];
 for(unsigned i=0;i<6;++i){blocks[8*i]=members[i];blocks[8*i+7]=std::uint64_t(i/3)<<32;}for(unsigned i=0;i<10;++i)sites[4*i]=i;
 unsigned status,emitted=0,owner_used=0,trial_used=0;bool overflow=false;
 auto run=[&](unsigned capacity){tileplace_wire_descriptor_enumerator::enumerate(0,units,2,members,blocks,positions,6,sites,10,10,10,10,10,roots,10,chain_roots,10,first,second,merged,6,descriptors,capacity,owners,384,trials,768,emitted,owner_used,trial_used,overflow,status);};
 run(128);assert(!status&&!overflow);unsigned macros=0;
 for(unsigned i=0;i<emitted;++i){auto d=descriptors+6*i;if(d[1]!=2)continue;++macros;assert(d[3]==2&&owners[d[2]]==0&&owners[d[2]+1]==1&&d[5]==6);unsigned targets[6]={5,6,7,0,1,2};for(unsigned j=0;j<6;++j){auto t=trials+3*(d[4]+j);assert(t[0]==members[j]&&t[1]==targets[j]&&t[2]==0);}}
 assert(macros>0);emitted=owner_used=trial_used=0;overflow=false;descriptors[0]=99;run(0);assert(status==5&&overflow&&!emitted&&descriptors[0]==99);
 std::cout<<"variable descriptor pools preserve six-block macro swap + capacity rejection PASS\n";
}
