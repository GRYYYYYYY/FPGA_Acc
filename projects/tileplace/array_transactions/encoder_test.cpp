#include "encoder.hpp"
#include "../cpp_snapshot/transactions.hpp"
#include <random>
#include <iostream>
int main(){
 using namespace tileplace_transaction_array;std::mt19937 rng(37);
 for(unsigned test=0;test<1000;++test){unsigned count=test%65;std::vector<tileplace_snapshot::Proposal> reference;
  std::vector<Record> records;std::vector<Location> sites;std::vector<unsigned> nets,units;
  for(unsigned i=0;i<count;++i){tileplace_snapshot::Proposal p;p.kind=i%2?"move":"macro_swap";p.trial[i*7+3]={int(rng()%11)-5,int(rng()%11)-5,int(rng()%3),int(rng()%3)};p.score=int(rng()%21)-15;
   for(unsigned j=0,n=rng()%4;j<n;++j)p.write_sites.insert({int(rng()%8),int(rng()%8),int(rng()%2),int(rng()%2)});
   for(unsigned j=0,n=rng()%4;j<n;++j)p.touched_nets.insert(rng()%20);
   std::set<unsigned> owners;for(unsigned j=0,n=rng()%3;j<n;++j)owners.insert(rng()%15);
   for(auto id:owners)p.units.push_back({id,id+100});
   std::reverse(p.units.begin(),p.units.end());
   Record r{p.score,i,{sites.size(),p.write_sites.size()},{nets.size(),p.touched_nets.size()},{units.size(),owners.size()}};
   for(auto q:p.write_sites)sites.push_back({q.x,q.y,q.subtile,q.layer});
   nets.insert(nets.end(),p.touched_nets.begin(),p.touched_nets.end());units.insert(units.end(),owners.begin(),owners.end());records.push_back(r);reference.push_back(p);
  }
  auto expected=tileplace_snapshot::select_transactions(reference);
  Encoded encoded(reference);auto actual=encoded.selected();
  if(actual.size()!=expected.size())return 1;
  for(unsigned i=0;i<actual.size();++i)if(actual[i].identity()!=expected[i].identity()||actual[i].score!=expected[i].score||actual[i].touched_nets!=expected[i].touched_nets||actual[i].write_sites!=expected[i].write_sites)return 2;
  for(unsigned i=0;i<reference.size();++i){const auto& id=encoded.records[i].identity;const auto& p=encoded.proposals[i];
   std::string kind(encoded.kinds.begin()+id.kind.offset,encoded.kinds.begin()+id.kind.offset+id.kind.count);if(kind!=p.kind)return 3;
   std::vector<tileplace_snapshot::Unit> decoded;
   for(std::uint64_t j=0;j<id.units.count;++j){auto r=encoded.identity_units[id.units.offset+j];decoded.emplace_back(encoded.members.begin()+r.offset,encoded.members.begin()+r.offset+r.count);}
   if(decoded!=p.units)return 4;
   tileplace_snapshot::Positions trial;for(std::uint64_t j=0;j<id.trial.count;++j){auto m=encoded.trials[id.trial.offset+j];trial[m.id]={m.target.x,m.target.y,m.target.subtile,m.target.layer};}
   if(trial!=p.trial)return 5;
  }

 }
 std::cout<<"1000 encoded transaction sets pass\n";
}
