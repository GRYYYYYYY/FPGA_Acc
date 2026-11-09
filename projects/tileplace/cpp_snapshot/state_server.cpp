#include "proposals.hpp"
#include "search_state.hpp"
#include <iostream>
using namespace tileplace_snapshot;
int main() {
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

 unsigned focus_count;std::cin>>focus_count;std::set<std::uint32_t> focus;
 while(focus_count--) {unsigned id;std::cin>>id;focus.insert(id);}
 if(!std::cin) return 2;
 constraints.reference=positions;
 for(const auto& u:units) if(u.size()>1) constraints.macros.push_back(u);
 SearchState state(positions,nets,{PressureSnapshot(edges),routed,focus},constraints);
 std::map<unsigned,SearchState> snapshots;
 std::cout<<"READY"<<std::endl;
 std::string command;
 while(std::cin>>command) {
  try {
   if(command=="QUIT") {std::cout<<"OK"<<std::endl;break;}
   if(command=="SAVE") {unsigned id;std::cin>>id;snapshots.insert_or_assign(id,state);std::cout<<"OK"<<std::endl;continue;}
   if(command=="RESTORE") {unsigned id;std::cin>>id;state=snapshots.at(id);std::cout<<"OK"<<std::endl;continue;}
   if(command=="DROP") {unsigned id;std::cin>>id;snapshots.erase(id);std::cout<<"OK"<<std::endl;continue;}
   if(command=="APPLY") {
    unsigned count;std::cin>>count;Positions changes;
    while(count--) {unsigned id;Point p;std::cin>>id>>p.x>>p.y>>p.subtile>>p.layer;changes[id]=p;}
    state.begin(changes);state.accept();std::cout<<"OK"<<std::endl;continue;
   }
   if(command=="FEEDBACK") {
    unsigned a,b,c;std::cin>>a>>b>>c;
    std::vector<Edge> next_edges(a);for(auto& e:next_edges)std::cin>>e.x0>>e.y0>>e.x1>>e.y1>>e.weight;
    std::vector<Connection> next_routed(b);for(auto& e:next_routed)std::cin>>e.source>>e.sink>>e.weight;
    std::set<std::uint32_t> next_focus;while(c--) {unsigned id;std::cin>>id;next_focus.insert(id);}
    state.replace_feedback({PressureSnapshot(next_edges),next_routed,next_focus});std::cout<<"OK"<<std::endl;continue;
   }
   if(command=="DUMP") {
    std::cout<<state.positions().size()<<'\n';
    for(const auto& [id,p]:state.positions())std::cout<<id<<' '<<p.x<<' '<<p.y<<' '<<p.subtile<<' '<<p.layer<<'\n';
    std::cout<<"END"<<std::endl;continue;
   }
   if(command=="COLOR") {
    unsigned color,n;std::cin>>color>>n;std::set<ProposalIdentity> forbidden;
    while(n--) {
     std::string kind;unsigned count;std::cin>>kind>>count;std::vector<Unit> moved(count);
     for(auto& u:moved) {unsigned size;std::cin>>size;u.resize(size);for(auto& id:u)std::cin>>id;}
     std::cin>>count;Positions trial;
     while(count--) {unsigned id;Point p;std::cin>>id>>p.x>>p.y>>p.subtile>>p.layer;trial[id]=p;}
     forbidden.emplace(kind,moved,trial);
    }
    auto feedback=state.feedback();
    auto selected=propose_color(color,units,fixed,state.positions(),constraints,nets,feedback->routed,
                               feedback->pressure,config,feedback->focus,forbidden,guards);
    std::cout<<selected.size()<<'\n';
    for(const auto& p:selected) {
     std::cout<<p.kind<<' '<<p.score<<' '<<p.units.size();
     for(const auto& u:p.units) {std::cout<<' '<<u.size();for(auto id:u)std::cout<<' '<<id;}
     std::cout<<' '<<p.trial.size();for(const auto& [id,q]:p.trial)std::cout<<' '<<id<<' '<<q.x<<' '<<q.y<<' '<<q.subtile<<' '<<q.layer;
     std::cout<<'\n';
    }
    std::cout<<"END"<<std::endl;continue;
   }
   throw std::invalid_argument("unknown command");
  } catch(const std::exception& error) {std::cout<<"ERROR "<<error.what()<<std::endl;}
 }
}
