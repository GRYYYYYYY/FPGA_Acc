#include "touched_words.hpp"
#include <vector>
#include <set>
#include <random>
#include <iostream>
int main(){std::mt19937 rng(113);
 for(unsigned t=0;t<3000;++t){std::vector<std::uint64_t> nets,moves;std::vector<unsigned> members,expected;std::set<unsigned> changed;unsigned count=rng()%50,size=rng()%12;
 for(unsigned i=0;i<size;++i){unsigned id=rng()%80;changed.insert(id);moves.insert(moves.end(),{id,0,0});}
 for(unsigned i=0;i<count;++i){unsigned n=rng()%10;auto offset=members.size();bool hit=false;for(unsigned j=0;j<n;++j){auto id=rng()%80;members.push_back(id);hit|=changed.count(id);}nets.insert(nets.end(),{3*i+1,0,offset,n,0,0});if(hit)expected.push_back(3*i+1);}
 unsigned output[50],status;for(auto &x:output)x=99;auto n=tileplace_wire_pipeline::touched(nets.data(),count,members.data(),members.size(),moves.data(),size,output,50,status);if(status||n!=expected.size())return 1;for(unsigned i=0;i<n;++i)if(output[i]!=expected[i])return 2;
 if(!expected.empty()){for(auto &x:output)x=99;auto n=tileplace_wire_pipeline::touched(nets.data(),count,members.data(),members.size(),moves.data(),size,output,expected.size()-1,status);if(n||status!=2)return 3;for(auto x:output)if(x!=99)return 4;}
 }
 unsigned out=99,status;std::uint64_t bad[6]={1,0,UINT64_MAX,1,0,0};if(tileplace_wire_pipeline::touched(bad,1,nullptr,0,nullptr,0,&out,1,status)||status!=1||out!=99)return 5;
 if(tileplace_wire_pipeline::touched(nullptr,UINT64_MAX,nullptr,0,nullptr,0,&out,1,status)||status!=3||out!=99)return 6;
 std::cout<<"3000 touched-net sets and atomic capacity/CSR/scaling faults pass\n";
}
