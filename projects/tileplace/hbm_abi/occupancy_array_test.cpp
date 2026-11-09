#include "occupancy_array.hpp"
#include "../cpp_snapshot/placement.hpp"
#include <random>
#include <iostream>
int main(){
 using namespace tileplace_hbm;std::mt19937 rng(35);unsigned hits=0,misses=0;
 for(unsigned fixture=0;fixture<20;++fixture){
  std::map<tileplace_snapshot::Point,std::pair<unsigned,unsigned>> reference;
  for(unsigned i=0;i<200;++i){tileplace_snapshot::Point p{int(rng()%61)-30,int(rng()%61)-30,int(rng()%4),int(rng()%3)};reference[p]={i*17+3,i%13};}
  reference[{INT32_MIN,INT32_MAX,INT32_MIN,INT32_MAX}]={UINT32_MAX,12};
  std::vector<Block> blocks;std::vector<Location> positions;
  for(const auto& [p,owner]:reference){Block b{};b.id=owner.first;b.unit_id=owner.second;blocks.push_back(b);positions.push_back({p.x,p.y,p.subtile,p.layer});}
  for(unsigned q=0;q<200;++q){Location p;
   if(q%2==0)p=positions[q%positions.size()];else p={int(rng()%81)-40,int(rng()%81)-40,int(rng()%4),int(rng()%3)};
   auto actual=occupancy_array(blocks.data(),positions.data(),blocks.size(),p);
   auto found=reference.find({p.x,p.y,p.subtile,p.layer});
   if(found==reference.end()){if(actual.found||actual.block_id||actual.unit_id)return 1;++misses;}
   else{if(!actual.found||actual.block_id!=found->second.first||actual.unit_id!=found->second.second)return 2;++hits;}
  }
  auto edge=occupancy_array(blocks.data(),positions.data(),blocks.size(),{INT32_MIN,INT32_MAX,INT32_MIN,INT32_MAX});
  if(!edge.found||edge.block_id!=UINT32_MAX||edge.unit_id!=12)return 3;
 }
 auto empty=occupancy_array(nullptr,nullptr,0,{});if(empty.found||empty.block_id||empty.unit_id)return 4;
 std::cout<<"4000 owner queries: "<<hits<<" hits, "<<misses<<" misses; 20 extremes and empty pass\n";
}
