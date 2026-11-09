#include "cost_pair_array.hpp"
#include "../cpp_snapshot/net_cost.hpp"
#include <random>
#include <iostream>
int main(){
 using namespace tileplace_cost_array;std::mt19937 rng(71);
 for(unsigned q=0;q<2000;++q){
  Block blocks[4]{};Location positions[4]{};tileplace_snapshot::Positions before,after;
  for(unsigned i=0;i<4;++i){blocks[i].id=3+i*7;positions[i]={int(rng()%21)-10,int(rng()%21)-10,0,0};before[blocks[i].id]={positions[i].x,positions[i].y};}
  after=before;std::vector<TrialMove> moves;std::set<unsigned> changed;
  for(unsigned i=0;i<q%5;++i){Location p{int(rng()%31)-15,int(rng()%31)-15,0,0};moves.push_back({blocks[i].id,p});changed.insert(blocks[i].id);after[blocks[i].id]={p.x,p.y};}
  unsigned members[]={3,10,17,24};Connection connections[]={{3,24,rng()%10000},{10,17,rng()%10000}};
  Net nets[2]{};nets[0].id=5;nets[0].members={0,4};nets[0].connections={0,1};nets[1].id=20;nets[1].members={0,4};nets[1].connections={1,1};
  std::vector<unsigned> touched;std::vector<tileplace_snapshot::Net> reference;
  for(unsigned i=0;i<2;++i)if((q>>i)&1){touched.push_back(nets[i].id);tileplace_snapshot::Net n;n.members={3,10,17,24};auto c=connections[i];n.connections.push_back({c.source,c.sink,c.weight});reference.push_back(n);}
  Connection routed[]={{3,10,rng()%10000},{17,24,rng()%10000}};
  std::vector<tileplace_snapshot::Connection> rr;for(auto c:routed)rr.push_back({c.source,c.sink,c.weight});
  tileplace_snapshot::PressureSnapshot pressure({});auto expected=tileplace_snapshot::cost_pair(reference,changed,before,after,rr,pressure);
  auto actual=cost_pair_array(nets,2,touched.data(),touched.size(),blocks,positions,4,members,4,connections,2,nullptr,0,nullptr,0,routed,2,moves.data(),moves.size());
  if(actual.status||actual.reserved)return 1;
  for(unsigned i=0;i<4;++i)if(actual.before[i]!=expected.first[i]||actual.after[i]!=expected.second[i])return 2;
 }
 Block blocks[2]{};blocks[0].id=3;blocks[1].id=10;Location positions[]={{0,0,0,0},{2,0,0,0}};
 TrialMove moves[]={{3,{1,0,0,0}}};Connection routed[]={{3,10,UINT64_MAX}};unsigned touched=42;
 auto invalid=cost_pair_array(nullptr,0,&touched,1,blocks,positions,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,moves,1);
 auto overflow=cost_pair_array(nullptr,0,nullptr,0,blocks,positions,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,routed,1,moves,1);
 if(invalid.status!=1||overflow.status!=3)return 3;
 for(unsigned i=0;i<4;++i)if(invalid.before[i]||invalid.after[i]||overflow.before[i]||overflow.after[i])return 4;
 std::cout<<"2000 cost pairs and unknown-net/routed-overflow atomic errors pass\n";
}
