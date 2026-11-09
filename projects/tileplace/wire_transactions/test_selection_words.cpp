#include "../array_transactions/identity_selection.hpp"
#include "selection_words.hpp"
#include "../cpp_snapshot/transactions.hpp"
#include <random>
#include <iostream>
int main(){
 using namespace tileplace_transaction_array;std::mt19937 rng(37);
 for(unsigned test=0;test<1000;++test){unsigned count=test%65;std::vector<tileplace_snapshot::Proposal> reference;
  std::vector<IdentityRecord> records;std::vector<std::uint8_t> kinds;std::vector<Range> identity_units;std::vector<unsigned> members;std::vector<tileplace_hbm::TrialMove> trials;std::vector<Location> sites;std::vector<unsigned> nets,units;
  for(unsigned i=0;i<count;++i){tileplace_snapshot::Proposal p;p.kind=(i%2?"move":"swap");p.trial[i+100]={int(rng()%11)-5,int(rng()%11)-5,int(rng()%3),int(rng()%3)};p.score=int(rng()%21)-15;
   for(unsigned j=0,n=rng()%4;j<n;++j)p.write_sites.insert({int(rng()%8),int(rng()%8),int(rng()%2),int(rng()%2)});
   for(unsigned j=0,n=rng()%4;j<n;++j)p.touched_nets.insert(rng()%20);
   std::set<unsigned> owners;for(unsigned j=0,n=rng()%3;j<n;++j)owners.insert(rng()%15);
   for(auto id:owners)p.units.push_back({id});
   Identity identity{{kinds.size(),p.kind.size()},{identity_units.size(),p.units.size()},{trials.size(),p.trial.size()}};
   kinds.insert(kinds.end(),p.kind.begin(),p.kind.end());
   for(const auto& u:p.units){identity_units.push_back({members.size(),u.size()});members.insert(members.end(),u.begin(),u.end());}
   for(auto [id,q]:p.trial)trials.push_back({id,{q.x,q.y,q.subtile,q.layer}});
   IdentityRecord r{p.score,identity,{sites.size(),p.write_sites.size()},{nets.size(),p.touched_nets.size()},{units.size(),owners.size()}};
   for(auto q:p.write_sites)sites.push_back({q.x,q.y,q.subtile,q.layer});
   nets.insert(nets.end(),p.touched_nets.begin(),p.touched_nets.end());units.insert(units.end(),owners.begin(),owners.end());records.push_back(r);reference.push_back(p);
  }
  auto expected=tileplace_snapshot::select_transactions(reference);std::vector<unsigned> order(count),selected(count);unsigned status;
  auto n=select_identity(records.data(),count,kinds.data(),kinds.size(),identity_units.data(),identity_units.size(),members.data(),members.size(),trials.data(),trials.size(),sites.data(),sites.size(),nets.data(),nets.size(),units.data(),units.size(),order.data(),count,selected.data(),count,status);
  std::vector<std::uint64_t> rec,iu,tw,sw;
  for(auto r:records)rec.insert(rec.end(),{std::uint64_t(r.score),r.identity.kind.offset,r.identity.kind.count,r.identity.units.offset,r.identity.units.count,r.identity.trial.offset,r.identity.trial.count,r.sites.offset,r.sites.count,r.nets.offset,r.nets.count,r.units.offset,r.units.count});
  for(auto u:identity_units)iu.insert(iu.end(),{u.offset,u.count});
  auto pack=[](int a,int b){return std::uint32_t(a)|(std::uint64_t(std::uint32_t(b))<<32);};
  for(auto t:trials){auto p=t.target;tw.insert(tw.end(),{t.id,pack(p.x,p.y),pack(p.subtile,p.layer)});}
  for(auto p:sites)sw.insert(sw.end(),{pack(p.x,p.y),pack(p.subtile,p.layer)});
  std::vector<unsigned> wo(count),ws(count);unsigned st=0;
  auto wn=tileplace_wire_transactions::select(rec.data(),count,kinds.data(),kinds.size(),iu.data(),identity_units.size(),members.data(),members.size(),tw.data(),trials.size(),sw.data(),sites.size(),nets.data(),nets.size(),units.data(),units.size(),wo.data(),count,ws.data(),count,st);
  if(st||wn!=expected.size())return 9;
  for(unsigned i=0;i<wn;++i)if(reference[ws[i]].identity()!=expected[i].identity())return 10;
  if(status||n!=expected.size())return 1;
  for(unsigned i=0;i<n;++i)if(reference[selected[i]].identity()!=expected[i].identity())return 2;
 }
 IdentityRecord bad{-1,{{0,0},{0,0},{0,0}},{UINT64_MAX,1},{0,0},{0,0}};unsigned order=99,selected=99,status;
 auto call=[&](unsigned capacity){return select_identity(&bad,1,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,&order,capacity,&selected,1,status);};
 if(call(1)||status!=1||order!=99||selected!=99)return 3;
 bad.sites={0,0};if(call(0)||status!=2||order!=99||selected!=99)return 4;
 bad.identity.kind={UINT64_MAX,1};if(call(1)||status!=3||order!=99||selected!=99)return 5;
 bad.identity.kind={0,0};bad.identity.units={0,1};if(call(1)||status!=3||order!=99||selected!=99)return 6;
 bad.identity.units={0,0};bad.identity.trial={0,1};if(call(1)||status!=3||order!=99||selected!=99)return 7;
 bad.identity.trial={0,0};bad.identity.units={0,1};Range malformed{UINT64_MAX,1};
 if(select_identity(&bad,1,nullptr,0,&malformed,1,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,&order,1,&selected,1,status)||status!=3||order!=99||selected!=99)return 8;
 std::uint64_t wr[13]{};wr[0]=UINT64_MAX;unsigned wo=99,ws=99,st=0;unsigned faults=0;
 auto check=[&](unsigned expected,unsigned capacity=1){auto n=tileplace_wire_transactions::select(wr,1,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,&wo,capacity,&ws,1,st);if(n||st!=expected||wo!=99||ws!=99)return false;++faults;return true;};
 wr[7]=UINT64_MAX;wr[8]=1;if(!check(1))return 11;wr[7]=wr[8]=0;if(!check(2,0))return 12;
 for(unsigned offset:{1u,3u,5u}){wr[offset]=UINT64_MAX;wr[offset+1]=1;if(!check(3))return 13;wr[offset]=wr[offset+1]=0;}
 std::uint64_t malformed_words[2]={UINT64_MAX,1};wr[4]=1;
 auto n=tileplace_wire_transactions::select(wr,1,nullptr,0,malformed_words,1,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,&wo,1,&ws,1,st);if(n||st!=3||wo!=99||ws!=99)return 14;++faults;
 std::cout<<faults<<" atomic wire selector faults pass\n";
 std::cout<<"1000 wire full-identity transaction sets and 6 atomic faults pass\n";
}
