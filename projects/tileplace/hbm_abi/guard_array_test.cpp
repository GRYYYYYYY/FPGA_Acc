#include "guard_array.hpp"
#include "../cpp_snapshot/placement.hpp"
#include <random>
#include <iostream>
int main(){
 using namespace tileplace_hbm;std::mt19937 rng(34);unsigned accepted=0,rejected=0;
 Block blocks[8]{};Location positions[8]{};
 for(unsigned i=0;i<8;++i){blocks[i].id=3+i*7;positions[i]={int(i)-4,int(i%3)-2,0,0};}
 for(unsigned q=0;q<2000;++q){TrialMove moves[8];Location candidate[8];unsigned n=q%9;
  for(unsigned i=0;i<8;++i)candidate[i]=positions[i];
  for(unsigned i=0;i<n;++i){Location p{int(rng()%41)-20,int(rng()%41)-20,int(rng()%3),int(rng()%3)};moves[i]={blocks[i].id,p};candidate[i]=p;}
  if(q==0){n=2;moves[0]={blocks[0].id,{INT32_MIN,INT32_MIN,0,0}};moves[1]={blocks[1].id,{INT32_MAX,INT32_MAX,0,0}};candidate[0]=moves[0].target;candidate[1]=moves[1].target;}
  ArrayGuard guards[12];bool expected=true;
  for(unsigned j=0;j<12;++j){auto a=rng()%8,b=rng()%8;std::uint64_t maximum=rng()%60;guards[j]={blocks[a].id,blocks[b].id,maximum};
   if((a<n||b<n)&&tileplace_snapshot::distance({candidate[a].x,candidate[a].y,candidate[a].subtile,candidate[a].layer},{candidate[b].x,candidate[b].y,candidate[b].subtile,candidate[b].layer})>maximum)expected=false;
  }
  unsigned status;auto actual=guard_array(blocks,positions,8,moves,n,guards,12,status);
  if(status||actual!=expected)return 1;
  actual?++accepted:++rejected;
 }
 unsigned status;TrialMove bad{999,{}};ArrayGuard guard{3,999,UINT64_MAX};
 if(guard_array(blocks,positions,8,&bad,1,nullptr,0,status)||status!=1)return 2;
 TrialMove moved{3,{}};
 if(guard_array(blocks,positions,8,&moved,1,&guard,1,status)||status!=2)return 3;
 TrialMove extreme[2]={{3,{INT32_MIN,INT32_MIN,0,0}},{10,{INT32_MAX,INT32_MAX,0,0}}};ArrayGuard boundary{3,10,8589934590ULL};
 if(!guard_array(blocks,positions,8,extreme,2,&boundary,1,status)||status)return 4;
 --boundary.maximum;if(guard_array(blocks,positions,8,extreme,2,&boundary,1,status)||status)return 5;
 if(!accepted||!rejected)return 6;
 std::cout<<"2000 guard queries: "<<accepted<<" pass, "<<rejected<<" reject; 2 faults and 2 extreme threshold checks pass\n";
}
