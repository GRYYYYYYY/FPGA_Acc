#include "candidate_root_array.hpp"
#include "../cpp_snapshot/placement.hpp"
#include <random>
#include <iostream>
int main(){
 using namespace tileplace_hbm;
 std::mt19937 rng(31);unsigned checks=0;
 for(unsigned fixture=0;fixture<20;++fixture){
  std::map<tileplace_snapshot::Point,std::string> reference;
  for(unsigned i=0;i<500;++i){tileplace_snapshot::Point p{int(rng()%101)-50,int(rng()%101)-50,int(rng()%3),int(rng()%3)};reference[p]=std::to_string(rng()%3);}
  reference[{INT32_MIN,0,0,0}]="0";reference[{INT32_MAX,0,0,0}]="0";
  std::vector<Site> sites;for(const auto& [p,t]:reference)sites.push_back({{p.x,p.y,p.subtile,p.layer},unsigned(std::stoul(t)),{0,0,0}});
  for(unsigned q=0;q<100;++q){
   Location source{int(rng()%101)-50,int(rng()%101)-50,int(rng()%3),int(rng()%3)};
   if(q==0)source={INT32_MIN,0,0,0};
   if(q==1)source={INT32_MAX,0,0,0};
   auto type=rng()%3;int width=1+rng()%15,height=1+rng()%15;unsigned limit=rng()%33,status;
   Location outputs[32];auto count=candidate_root_array(sites.data(),sites.size(),source,type,width,height,limit,outputs,32,status);
   auto expected=tileplace_snapshot::candidate_roots({source.x,source.y,source.subtile,source.layer},std::to_string(type),reference,width,height,limit);
   if(status||count!=expected.size())return 1;
   for(unsigned i=0;i<count;++i)if(!(tileplace_snapshot::Point{outputs[i].x,outputs[i].y,outputs[i].subtile,outputs[i].layer}==expected[i]))return 2;
   ++checks;
  }
 }
 Location out[1];unsigned status;
 if(candidate_root_array(nullptr,0,{},0,0,1,1,out,1,status)||status!=1)return 3;
 if(candidate_root_array(nullptr,0,{},0,1,1,2,out,1,status)||status!=2)return 4;
 std::cout<<checks<<" root-order queries and 2 errors pass\n";
}
