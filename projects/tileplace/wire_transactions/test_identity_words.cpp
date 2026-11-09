#include "../array_transactions/identity.hpp"
#include "identity_words.hpp"
#include "../cpp_snapshot/transactions.hpp"
#include <random>
#include <iostream>
int main(){
 using namespace tileplace_transaction_array;std::mt19937 rng(38);
 std::vector<std::uint8_t> kinds;std::vector<Range> units;std::vector<unsigned> members;std::vector<tileplace_hbm::TrialMove> trials;
 std::vector<Identity> identities;std::vector<tileplace_snapshot::Proposal> reference;
 const char* names[]={"chain2","chain3","macro_swap","move","swap","","move_long"};
 for(unsigned i=0;i<500;++i){tileplace_snapshot::Proposal p;p.kind=names[rng()%7];
  for(unsigned j=0,n=rng()%4;j<n;++j){tileplace_snapshot::Unit u;for(unsigned k=0,m=rng()%5;k<m;++k)u.push_back(rng()%100);std::sort(u.begin(),u.end());p.units.push_back(u);}std::sort(p.units.begin(),p.units.end());
  for(unsigned j=0,n=rng()%6;j<n;++j)p.trial[rng()%100]={int(rng()%31)-15,int(rng()%31)-15,int(rng()%7)-3,int(rng()%7)-3};
  Identity id{{kinds.size(),p.kind.size()},{units.size(),p.units.size()},{trials.size(),p.trial.size()}};kinds.insert(kinds.end(),p.kind.begin(),p.kind.end());
  for(auto&u:p.units){units.push_back({members.size(),u.size()});members.insert(members.end(),u.begin(),u.end());}
  for(auto [block,q]:p.trial)trials.push_back({block,{q.x,q.y,q.subtile,q.layer}});
  identities.push_back(id);reference.push_back(p);
 }
 std::vector<std::uint64_t> iw,uw,tw;
 for(auto id:identities)iw.insert(iw.end(),{id.kind.offset,id.kind.count,id.units.offset,id.units.count,id.trial.offset,id.trial.count});
 for(auto u:units)uw.insert(uw.end(),{u.offset,u.count});
 for(auto t:trials){auto p=t.target;tw.insert(tw.end(),{t.id,std::uint32_t(p.x)|(std::uint64_t(std::uint32_t(p.y))<<32),std::uint32_t(p.subtile)|(std::uint64_t(std::uint32_t(p.layer))<<32)});}
 for(unsigned q=0;q<5000;++q){auto a=rng()%500,b=q%10==0?a:rng()%500;
  int expected=reference[a].identity()<reference[b].identity()?-1:reference[b].identity()<reference[a].identity()?1:0;
  if(tileplace_wire_transactions::identity(iw.data()+6*a,iw.data()+6*b,kinds.data(),uw.data(),members.data(),tw.data())!=expected)return 2;
  if(identity_compare(identities[a],identities[b],kinds.data(),units.data(),members.data(),trials.data())!=expected)return 1;
 }
 std::cout<<"5000 wire complete identity comparisons pass\n";
}
