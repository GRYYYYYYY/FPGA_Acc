#include "macro_translation_array.hpp"
#include "../cpp_snapshot/placement.hpp"
#include <random>
#include <iostream>
int main(){
 std::mt19937 rng(33);unsigned checked=0;
 for(unsigned n=1;n<=20;++n){
  std::vector<tileplace_hbm::Block> blocks(n);std::vector<tileplace_hbm::Location> positions(n);
  tileplace_snapshot::Positions reference;std::vector<unsigned> members;
  for(unsigned i=0;i<n;++i){blocks[i].id=i*7+3;auto&p=positions[i];p={int(rng()%41)-20,int(rng()%41)-20,int(rng()%41)-20,int(rng()%41)-20};reference[blocks[i].id]={p.x,p.y,p.subtile,p.layer};members.push_back(blocks[i].id);}
  for(unsigned q=0;q<100;++q){tileplace_hbm::Location target{int(rng()%61)-30,int(rng()%61)-30,int(rng()%61)-30,int(rng()%61)-30};
   std::vector<tileplace_hbm::TrialMove> out(n);unsigned status;
   auto count=tileplace_hbm::macro_translation_array(blocks.data(),positions.data(),n,members.data(),n,target,out.data(),n,status);
   auto expected=tileplace_snapshot::translated(members,{target.x,target.y,target.subtile,target.layer},reference);
   if(status||count!=n)return 1;
   for(auto&m:out)if(!(tileplace_snapshot::Point{m.target.x,m.target.y,m.target.subtile,m.target.layer}==expected.at(m.id)))return 2;
   ++checked;
  }
 }
 tileplace_hbm::Block blocks[2]{};blocks[0].id=3;blocks[1].id=7;
 tileplace_hbm::Location positions[2]{};unsigned members[2]={3,7},status;
 tileplace_hbm::TrialMove out[2]={{999,{1,2,3,4}},{999,{1,2,3,4}}};
 for(unsigned fault=0;fault<11;++fault){positions[0]={};positions[1]={};members[1]=7;
  tileplace_hbm::Location target{};unsigned size=2,capacity=2,expected;
  if(fault==0){size=0;expected=1;}else if(fault==1){capacity=1;expected=2;}else if(fault==2){members[1]=999;expected=3;}
  else{expected=4;int* coordinates= (fault-3)%4==0?&positions[1].x:(fault-3)%4==1?&positions[1].y:(fault-3)%4==2?&positions[1].subtile:&positions[1].layer;
   *coordinates=fault<7?INT32_MAX:INT32_MIN;int step=fault<7?1:-1;target={step,step,step,step};}
  if(tileplace_hbm::macro_translation_array(blocks,positions,2,members,size,target,out,capacity,status)||status!=expected)return 3;
  for(auto&m:out)if(m.id!=999||!tileplace_hbm::location_equal(m.target,{1,2,3,4}))return 4;
 }
 std::cout<<checked<<" macro translations and 11 atomic faults pass\n";
}
