#include "enumerate_words.hpp"
#include <set>
#include <iostream>
int main(){std::uint64_t units[12]={0,1,0,0,1,1,0,0,2,1,0,0},blocks[24]{},positions[6]={0,0,1,0,2,0},sites[16]{},roots[8],chain_roots[8],first[9],second[9],merged[9];unsigned members[3]={2,5,8};for(unsigned i=0;i<3;++i){blocks[8*i]=members[i];blocks[8*i+7]=std::uint64_t(i)<<32;}for(unsigned i=0;i<4;++i)sites[4*i]=i;std::set<unsigned> kinds;unsigned emitted=0,status;
 auto emit=[&](unsigned kind,const unsigned*,unsigned,const std::uint64_t* moves,unsigned n){kinds.insert(kind);++emitted;for(unsigned i=1;i<n;++i)if(moves[3*i]<=moves[3*(i-1)])throw 1;};
 tileplace_wire_enumerator::enumerate(0,units,3,members,blocks,positions,3,sites,4,4,4,4,4,roots,4,chain_roots,4,first,second,merged,3,emit,status);
 if(status||!kinds.count(0)||!kinds.count(1)||!kinds.count(3)||!kinds.count(4))return 1;std::cout<<emitted<<" integer branch trials emitted; move/swap/chain2/chain3 covered (macro reference pending)\n";}
