#include "../hbm_abi/callback_proposals.hpp"
#include "../wire_control_commit/host_snapshot_words.hpp"
#include "host_scratch_words.hpp"
#include "../wire_control_commit/host_propose.hpp"
#include "../wire_transactions/encoder_words.hpp"
#include <fstream>
#include <iostream>
using namespace tileplace_snapshot;
using ProposalIdentity=std::tuple<std::string,std::vector<Unit>,Positions>;
int main(int argc,char**argv){
 if(argc!=2)return 2;
 try {
 std::ifstream file(argv[1],std::ios::binary);if(!file)return 2;
 std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});
 tileplace_wire_control_commit::HostSnapshotWords snapshot(bytes);
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
 if(!color)throw std::invalid_argument("full color query requires color selector");
 auto input=snapshot.input();input.color=selector;input.width=config.page_width;input.height=config.page_height;input.limit=config.candidate_limit;input.chain_limit=config.chain_limit;input.weights=config.weights.data();
 std::vector<std::uint64_t> guard_words;for(const auto& guard:guards)guard_words.insert(guard_words.end(),{std::uint64_t(guard.source)|(std::uint64_t(guard.sink)<<32),guard.maximum});input.guards=guard_words.data();input.guard_count=guards.size();
 std::vector<Proposal> placeholders;for(const auto& id:forbidden){Proposal p;p.kind=std::get<0>(id);p.units=std::get<1>(id);p.trial=std::get<2>(id);placeholders.push_back(p);}
 tileplace_wire_transactions::Encoded blocked(std::move(placeholders));std::vector<std::uint64_t> identities;for(unsigned i=0;i<blocked.proposals.size();++i){auto r=blocked.rw.data()+13ULL*i;identities.insert(identities.end(),r+1,r+7);}
 tileplace_wire_control_commit::ExternalForbidden external{identities.data(),unsigned(blocked.proposals.size()),{blocked.kinds.data(),blocked.kinds.size(),blocked.iw.data(),blocked.iw.size()/2,blocked.members.data(),blocked.members.size(),blocked.tw.data(),blocked.tw.size()/3}};input.external_forbidden=&external;
 tileplace_wire_control_commit::HostColorScratch scratch(input);auto proposed=tileplace_wire_control_commit::propose(input,scratch.view());auto& proposals=proposed.proposals;
 for(const auto& p:proposals) {
  std::cout<<p.kind<<' '<<p.score<<' '<<p.units.size();
  for(const auto& u:p.units) {std::cout<<' '<<u.size();for(auto id:u)std::cout<<' '<<id;}
  std::cout<<' '<<p.trial.size();for(const auto& [id,q]:p.trial) std::cout<<' '<<id<<' '<<q.x<<' '<<q.y<<' '<<q.subtile<<' '<<q.layer;
  std::cout<<'\n';
 }
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
