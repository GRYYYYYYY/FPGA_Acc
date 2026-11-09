#include "owners_words.hpp"
#include <random>
#include <set>
#include <iostream>
int main(){std::mt19937 rng(149);unsigned multi=0,none=0;
 for(unsigned t=0;t<3000;++t){std::uint64_t blocks[128]{},positions[32],moves[12]{};unsigned own[4]={2,5,8,11};std::set<unsigned> expected;
 for(unsigned i=0;i<16;++i){blocks[8*i]=3*i+2;blocks[8*i+7]=std::uint64_t(i/4)<<32;tileplace_wire_candidates::store(positions+2*i,{int(i),int(i%3),int(i%2),int(i%4)});}
 for(unsigned i=0;i<4;++i){unsigned target=rng()%20;moves[3*i]=own[i];tileplace_hbm::Location p=target<16?tileplace_wire_candidates::location(positions+2*target):tileplace_hbm::Location{99,99,0,0};tileplace_wire_candidates::store(moves+3*i+1,p);if(target>=4&&target<16)expected.insert(target/4);}
 auto r=tileplace_wire_enumeration::owners(blocks,positions,16,own,4,moves,4);if(r.status||r.count!=std::min(std::size_t(2),expected.size())||(expected.size()==1&&r.unit!=*expected.begin()))return 1;multi+=r.count==2;none+=r.count==0;
 }
 std::uint64_t block[8]={2},pos[2]{},move[3]={999,0,0};unsigned own=2;auto r=tileplace_wire_enumeration::owners(block,pos,1,&own,1,move,1);if(r.status!=1||r.count)return 2;r=tileplace_wire_enumeration::owners(nullptr,nullptr,UINT64_MAX,nullptr,0,nullptr,0);if(r.status!=2||r.count)return 3;
 std::cout<<"3000 owner classifications pass; multiple="<<multi<<" empty="<<none<<"; unknown/scaling faults pass\n";
}
