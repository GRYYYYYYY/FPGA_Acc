#include "wire_search.hpp"
#include <fstream>
#include <iostream>
using namespace tileplace_snapshot;
int main(int argc,char**argv){
 if(argc!=2)return 2;
 try {
 std::ifstream file(argv[1],std::ios::binary);if(!file)return 2;
 std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});
 tileplace_hbm::WireCostSearch search(bytes);
 unsigned selector,color,ng,n;CallbackProposalConfig config;
 std::cin>>selector>>color>>config.page_width>>config.page_height>>config.candidate_limit>>config.chain_limit;
 for(auto&w:config.weights)std::cin>>w;
 std::cin>>ng;std::vector<CallbackGuard> guards(ng);
 for(auto&g:guards)std::cin>>g.source>>g.sink>>g.maximum;
 std::cin>>n;std::set<ProposalIdentity> forbidden;
 while(n--){std::string kind;unsigned count;std::cin>>kind>>count;std::vector<Unit> moved(count);
  for(auto&u:moved){unsigned size;std::cin>>size;u.resize(size);for(auto&id:u)std::cin>>id;}
  std::cin>>count;Positions trial;
  while(count--){unsigned id;Point p;std::cin>>id>>p.x>>p.y>>p.subtile>>p.layer;trial[id]=p;}
  forbidden.emplace(kind,moved,trial);
 }
 if(!std::cin||color>1)return 2;
 auto proposals=search.proposals(selector,color,config,forbidden,guards);
 for(const auto& p:proposals) {
  std::cout<<p.kind<<' '<<p.score<<' '<<p.units.size();
  for(const auto& u:p.units) {std::cout<<' '<<u.size();for(auto id:u)std::cout<<' '<<id;}
  std::cout<<' '<<p.trial.size();for(const auto& [id,q]:p.trial) std::cout<<' '<<id<<' '<<q.x<<' '<<q.y<<' '<<q.subtile<<' '<<q.layer;
  std::cout<<'\n';
 }
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
