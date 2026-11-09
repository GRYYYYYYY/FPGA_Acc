#include "occupancy_shape_words.hpp"
#include "../hbm_abi/macro_shape_array.hpp"
#include <random>
#include <iostream>
int main(){using namespace tileplace_hbm;std::mt19937 rng(109);unsigned matches=0;
 for(unsigned t=0;t<4000;++t){Block blocks[8]{};Location p[8];std::uint64_t bw[64]{},pw[16],query[2];unsigned a[4]={2,5,8,11},b[4]={14,17,20,23};unsigned na=1+rng()%4,nb=na;
 for(unsigned i=0;i<8;++i){blocks[i].id=3*i+2;blocks[i].type_id=i%3;blocks[i].unit_id=i/4;p[i]={int(i%4)*3,int(rng()%11),int(rng()%7)-3,int(i/4)};}
 if(t%2==0)for(unsigned i=0;i<4;++i){p[4+i]={p[i].x+10,p[i].y-4,p[i].subtile+3,p[i].layer+2};blocks[4+i].type_id=blocks[i].type_id;}
 if(t%11==0){p[0].x=INT32_MIN;p[1].x=INT32_MAX;}if(t%13==0)b[nb-1]=999;if(t%17==0)na=0;if(t%19==0)nb=4;
 for(unsigned i=0;i<8;++i){bw[8*i]=blocks[i].id|(std::uint64_t(blocks[i].type_id)<<32);bw[8*i+7]=std::uint64_t(blocks[i].unit_id)<<32;tileplace_wire_candidates::store(pw+2*i,p[i]);}
 unsigned x,y;bool e=macro_shape_array(blocks,p,8,a,na,b,nb,x),f=tileplace_wire_checks::shape(bw,pw,8,a,na,b,nb,y);if(e!=f||x!=y)return 1;matches+=f;
 auto q=t%3?p[rng()%8]:Location{999,999,0,0};tileplace_wire_candidates::store(query,q);auto expected=occupancy_array(blocks,p,8,q),actual=tileplace_wire_checks::occupant(bw,pw,8,query,y);if(y||expected.found!=actual.found||expected.block_id!=actual.block_id||expected.unit_id!=actual.unit_id)return 2;
 }
 unsigned st,id=0;std::uint64_t q[2]{};auto o=tileplace_wire_checks::occupant(nullptr,nullptr,UINT64_MAX,q,st);if(st!=1||o.found)return 3;
 if(tileplace_wire_checks::shape(nullptr,nullptr,UINT64_MAX,&id,1,&id,1,st)||st!=3)return 4;
 std::cout<<"4000 shape and occupancy differential cases pass; matching shapes="<<matches<<"; 2 scaling faults pass\n";
}
