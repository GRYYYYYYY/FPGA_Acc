#include "translation_words.hpp"
#include <random>
#include <iostream>
int main(){std::mt19937 rng(101);using namespace tileplace_hbm;
 for(unsigned t=0;t<3000;++t){Block blocks[8]{};Location positions[8];std::uint64_t bw[64]{},pw[16],target[2],out[24];TrialMove expected[8];std::uint32_t members[8];
 for(unsigned i=0;i<8;++i){blocks[i].id=3*i+2;bw[8*i]=blocks[i].id;members[i]=blocks[i].id;positions[i]={int(rng()%101)-50,int(rng()%101)-50,int(rng()%11)-5,int(rng()%11)-5};tileplace_wire_candidates::store(pw+2*i,positions[i]);}
 Location q{int(rng()%101)-50,int(rng()%101)-50,int(rng()%11)-5,int(rng()%11)-5};if(t%7==0)q.x=INT32_MAX;if(t%11==0)q.layer=INT32_MIN;tileplace_wire_candidates::store(target,q);unsigned size=1+rng()%8;if(t%13==0)members[size-1]=999;
 for(auto &w:out)w=99;unsigned a,b;auto n=macro_translation_array(blocks,positions,8,members,size,q,expected,8,a);auto m=tileplace_wire_candidates::translate(bw,pw,8,members,size,target,out,8,b);if(n!=m||a!=b)return 1;
 if(a){for(auto w:out)if(w!=99)return 2;}else for(unsigned i=0;i<n;++i){auto p=tileplace_wire_candidates::location(out+3*i+1),e=expected[i].target;if(out[3*i]!=expected[i].id||p.x!=e.x||p.y!=e.y||p.subtile!=e.subtile||p.layer!=e.layer)return 3;}
 }
 std::uint64_t target[2]{},out[3]={99,99,99};unsigned id=0,status;
 if(tileplace_wire_candidates::translate(nullptr,nullptr,UINT64_MAX,&id,1,target,out,1,status)||status!=5)return 4;for(auto w:out)if(w!=99)return 5;
 std::cout<<"3000 translation word differential cases and scaling atomic error pass\n";
}
