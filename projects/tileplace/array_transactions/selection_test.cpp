#include "selection.hpp"
#include "../cpp_snapshot/transactions.hpp"
#include <random>
#include <iostream>
int main(){
 using namespace tileplace_transaction_array;std::mt19937 rng(37);
 for(unsigned test=0;test<1000;++test){unsigned count=test%65;std::vector<tileplace_snapshot::Proposal> reference;
  std::vector<Record> records;std::vector<Location> sites;std::vector<unsigned> nets,units;
  for(unsigned i=0;i<count;++i){tileplace_snapshot::Proposal p;p.kind=std::to_string(1000+i);p.score=int(rng()%21)-15;
   for(unsigned j=0,n=rng()%4;j<n;++j)p.write_sites.insert({int(rng()%8),int(rng()%8),int(rng()%2),int(rng()%2)});
   for(unsigned j=0,n=rng()%4;j<n;++j)p.touched_nets.insert(rng()%20);
   std::set<unsigned> owners;for(unsigned j=0,n=rng()%3;j<n;++j)owners.insert(rng()%15);
   for(auto id:owners)p.units.push_back({id});
   Record r{p.score,i,{sites.size(),p.write_sites.size()},{nets.size(),p.touched_nets.size()},{units.size(),owners.size()}};
   for(auto q:p.write_sites)sites.push_back({q.x,q.y,q.subtile,q.layer});
   nets.insert(nets.end(),p.touched_nets.begin(),p.touched_nets.end());units.insert(units.end(),owners.begin(),owners.end());records.push_back(r);reference.push_back(p);
  }
  auto expected=tileplace_snapshot::select_transactions(reference);std::vector<unsigned> order(count),selected(count);unsigned status;
  auto n=select(records.data(),count,sites.data(),sites.size(),nets.data(),nets.size(),units.data(),units.size(),order.data(),count,selected.data(),count,status);
  if(status||n!=expected.size())return 1;
  for(unsigned i=0;i<n;++i)if(reference[selected[i]].kind!=expected[i].kind)return 2;
 }
 Record bad{-1,0,{UINT64_MAX,1},{0,0},{0,0}};unsigned order=99,selected=99,status;
 if(select(&bad,1,nullptr,0,nullptr,0,nullptr,0,&order,1,&selected,1,status)||status!=1||order!=99||selected!=99)return 3;
 bad.sites={0,0};if(select(&bad,1,nullptr,0,nullptr,0,nullptr,0,&order,0,&selected,1,status)||status!=2||order!=99||selected!=99)return 4;
 std::cout<<"1000 transaction sets and 2 atomic faults pass\n";
}
