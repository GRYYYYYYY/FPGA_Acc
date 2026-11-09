#include "guard_words.hpp"
#include "../hbm_abi/guard_array.hpp"
#include <random>
#include <iostream>
int main(){using namespace tileplace_hbm;std::mt19937 rng(107);unsigned rejected=0,errors=0;
 for(unsigned t=0;t<4000;++t){Block blocks[8]{};Location positions[8];TrialMove moves[4];ArrayGuard guards[6];std::uint64_t bw[64]{},pw[16],mw[12]{},gw[12];unsigned size=rng()%5;
 for(unsigned i=0;i<8;++i){blocks[i].id=3*i+2;bw[8*i]=blocks[i].id;positions[i]={int(rng()%101)-50,int(rng()%101)-50,int(rng()%7)-3,int(rng()%7)-3};tileplace_wire_candidates::store(pw+2*i,positions[i]);}
 for(unsigned i=0;i<size;++i){moves[i]={blocks[i].id,{int(rng()%101)-50,int(rng()%101)-50,int(rng()%7)-3,int(rng()%7)-3}};if(t%17==0&&i+1==size)moves[i].id=999;mw[3*i]=moves[i].id;tileplace_wire_candidates::store(mw+3*i+1,moves[i].target);}
 for(unsigned i=0;i<6;++i){guards[i]={blocks[rng()%8].id,blocks[rng()%8].id,rng()%150};if(t%19==0)guards[i].sink=999;gw[2*i]=guards[i].source|(std::uint64_t(guards[i].sink)<<32);gw[2*i+1]=guards[i].maximum;}
 unsigned a,b;auto x=guard_array(blocks,positions,8,moves,size,guards,6,a),y=tileplace_wire_checks::guards(bw,pw,8,mw,size,gw,6,b);if(x!=y||a!=b)return 1;rejected+=!y&&!b;errors+=bool(b);
 }
 unsigned status;if(tileplace_wire_checks::guards(nullptr,nullptr,UINT64_MAX,nullptr,0,nullptr,0,status)||status!=3)return 2;
 if(tileplace_wire_checks::guards(nullptr,nullptr,0,nullptr,0,nullptr,UINT64_MAX,status)||status!=3)return 3;
 std::cout<<"4000 guard word differential cases pass; legal rejections="<<rejected<<" input errors="<<errors<<"; 2 scaling faults pass\n";
}
