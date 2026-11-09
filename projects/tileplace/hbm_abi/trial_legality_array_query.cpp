#include "trial_legality_array.hpp"
#include <vector>
#include <iostream>
using namespace tileplace_hbm;
int main(){
 unsigned nb,ns,nr,nq;std::cin>>nb>>ns>>nr>>nq;
 std::vector<Block> blocks(nb);std::vector<Location> positions(nb);std::vector<Site> sites(ns);std::vector<Region> regions(nr);
 for(auto&b:blocks){std::cin>>b.id>>b.type_id>>b.initial.x>>b.initial.y>>b.initial.subtile>>b.initial.layer>>b.regions.offset>>b.regions.count;for(auto&v:b.fixed)std::cin>>v;std::cin>>b.fixed_mask>>b.unit_id;}
 for(auto&p:positions)std::cin>>p.x>>p.y>>p.subtile>>p.layer;
 for(auto&s:sites){std::cin>>s.location.x>>s.location.y>>s.location.subtile>>s.location.layer>>s.type_id;for(auto&r:s.reserved)std::cin>>r;}
 for(auto&r:regions)std::cin>>r.xmin>>r.ymin>>r.xmax>>r.ymax>>r.layer_low>>r.layer_high>>r.subtile>>r.reserved;
 while(nq--){unsigned n;std::cin>>n;std::vector<TrialMove> moves(n);
  for(auto&m:moves)std::cin>>m.id>>m.target.x>>m.target.y>>m.target.subtile>>m.target.layer;
  if(!std::cin)return 2;
  unsigned status;
  bool valid=trial_legality_array(blocks.data(),positions.data(),nb,sites.data(),ns,regions.data(),nr,moves.data(),n,status);
  std::cout<<valid<<' '<<status<<'\n';
 }
}
