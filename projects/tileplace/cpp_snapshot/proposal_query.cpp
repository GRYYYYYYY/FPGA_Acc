#include "proposals.hpp"
#include <iostream>
using namespace tileplace_snapshot;
int main(int argc,char** argv) {
 unsigned nb,ns,nu,nn,ne,nr,ng,root; ProposalConfig config;
 std::cin>>nb>>ns>>nu>>nn>>ne>>nr>>ng>>root;
 std::cin>>config.page_width>>config.page_height>>config.candidate_limit>>config.chain_limit;
 for(auto& w:config.weights) std::cin>>w;
 Positions positions; PlacementConstraints constraints;
 for(unsigned i=0;i<nb;++i) {
  unsigned id; Point p; Block b; int regions; std::cin>>id>>p.x>>p.y>>p.subtile>>p.layer>>b.type>>regions;
  if(regions>=0) {b.regions=std::vector<Region>(regions); for(auto& r:*b.regions) std::cin>>r.xmin>>r.ymin>>r.xmax>>r.ymax>>r.layer_low>>r.layer_high>>r.subtile;}
  for(auto& f:b.fixed) {int flag,value; std::cin>>flag>>value; if(flag) f=value;}
  positions[id]=p; constraints.blocks[id]=b;
 }
 for(unsigned i=0;i<ns;++i) {Point p; std::string type; std::cin>>p.x>>p.y>>p.subtile>>p.layer>>type; constraints.sites[p]=type;}
 std::vector<Unit> units(nu); std::set<Unit> fixed;
 for(auto& u:units) {unsigned n,flag; std::cin>>n>>flag; u.resize(n);for(auto& id:u) std::cin>>id; if(flag) fixed.insert(u);}
 std::vector<Net> nets(nn);
 for(auto& net:nets) {unsigned m,c;std::cin>>m>>c;net.members.resize(m);net.connections.resize(c);for(auto& id:net.members) std::cin>>id;for(auto& e:net.connections)std::cin>>e.source>>e.sink>>e.weight;}
 std::vector<Edge> edges(ne);for(auto& e:edges)std::cin>>e.x0>>e.y0>>e.x1>>e.y1>>e.weight;
 std::vector<Connection> routed(nr);for(auto& e:routed)std::cin>>e.source>>e.sink>>e.weight;
 std::vector<Guard> guards(ng);for(auto& g:guards)std::cin>>g.source>>g.sink>>g.maximum;
 if(!std::cin) return 2;
 std::vector<Proposal> proposals;
 if(argc==2 && std::string(argv[1])=="--color") {
  unsigned n;std::cin>>n;std::set<std::uint32_t> focus;
  while(n--) {unsigned id;std::cin>>id;focus.insert(id);}
  std::set<ProposalIdentity> forbidden;
  if(argc==2) {
   std::cin>>n;
   while(n--) {
    std::string kind; unsigned count; std::cin>>kind>>count;std::vector<Unit> moved(count);
    for(auto& u:moved) {unsigned size;std::cin>>size;u.resize(size);for(auto& id:u)std::cin>>id;}
    std::cin>>count;Positions trial;
    while(count--) {unsigned id;Point p;std::cin>>id>>p.x>>p.y>>p.subtile>>p.layer;trial[id]=p;}
    forbidden.emplace(kind,moved,trial);
   }
  }
  if(!std::cin) return 2;
  proposals=propose_color(root,units,fixed,positions,constraints,nets,routed,PressureSnapshot(edges),config,focus,forbidden,guards);
 } else proposals=proposals_for_unit(units.at(root),units,fixed,positions,constraints,nets,routed,PressureSnapshot(edges),config,guards);
 for(const auto& p:proposals) {
  std::cout<<p.kind<<' '<<p.score<<' '<<p.units.size();
  for(const auto& u:p.units) {std::cout<<' '<<u.size();for(auto id:u)std::cout<<' '<<id;}
  std::cout<<' '<<p.trial.size();for(const auto& [id,q]:p.trial) std::cout<<' '<<id<<' '<<q.x<<' '<<q.y<<' '<<q.subtile<<' '<<q.layer;
  std::cout<<'\n';
 }
}
