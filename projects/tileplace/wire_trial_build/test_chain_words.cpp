#include "chain_words.hpp"
#include <random>
#include <algorithm>
#include <map>
#include <array>
#include <iostream>
int main(){std::mt19937 rng(157);for(unsigned t=0;t<3000;++t){std::uint64_t blocks[64]{},positions[16],target[2]={rng(),rng()},next[2]={rng(),rng()},out[9];for(unsigned i=0;i<8;++i){blocks[8*i]=3*i+2;positions[2*i]=rng();positions[2*i+1]=rng();}unsigned ids[3]={2,5,8};std::shuffle(ids,ids+3,rng);unsigned count=2+t%2;std::map<unsigned,std::array<std::uint64_t,2>> expected;expected[ids[0]]={target[0],target[1]};expected[ids[1]]={next[0],next[1]};if(count==3){auto index=(ids[0]-2)/3;expected[ids[2]]={positions[2*index],positions[2*index+1]};}unsigned status;auto n=tileplace_wire_trial_build::chain(blocks,positions,8,ids,count,target,next,out,3,status);if(n!=count||status)return 1;unsigned i=0;for(auto [id,p]:expected){if(out[3*i]!=id||out[3*i+1]!=p[0]||out[3*i+2]!=p[1])return 2;++i;}}
 std::uint64_t blocks[16]={2},positions[4]{},target[2]{},next[2]{},out[9];blocks[8]=5;unsigned ids[3]={2,5,8},status;
 auto check=[&](unsigned count,unsigned cap,std::uint64_t bc,unsigned expected){for(auto &x:out)x=99;auto n=tileplace_wire_trial_build::chain(blocks,positions,bc,ids,count,target,next,out,cap,status);if(n||status!=expected)return false;for(auto x:out)if(x!=99)return false;return true;};
 if(!check(1,3,2,1)||!check(2,1,2,2)||!check(3,3,2,3)||!check(2,3,UINT64_MAX,5))return 3;ids[1]=2;if(!check(2,3,2,4))return 4;
 std::cout<<"3000 chain2/chain3 trial constructions pass\n";}
