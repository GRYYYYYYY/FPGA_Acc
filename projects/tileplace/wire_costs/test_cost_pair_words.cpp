#include "../array_costs/cost_pair_array.hpp"
#include "cost_pair_words.hpp"
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
  std::vector<PrefixLine> lines;std::vector<PrefixEntry> entries;std::vector<tileplace_snapshot::Edge> edges;std::vector<std::uint64_t> lw,ew;
  for(int axis=0;axis<2;++axis)for(int line=-2;line<=2;++line){auto offset=entries.size();std::uint64_t total=0;
   for(int coordinate=-3;coordinate<=3;++coordinate){auto weight=rng()%100000;entries.push_back({coordinate,0,total});total+=weight;
    edges.push_back(axis==0?tileplace_snapshot::Edge{coordinate,line,coordinate+1,line,weight}:tileplace_snapshot::Edge{line,coordinate,line,coordinate+1,weight});}
   lines.push_back({axis,line,total,{offset,7}});
  }
  for(auto l:lines){lw.push_back(std::uint32_t(l.axis)|(std::uint64_t(std::uint32_t(l.line))<<32));lw.push_back(l.total_pressure);lw.push_back(l.entries.offset);lw.push_back(l.entries.count);}
  for(auto e:entries){ew.push_back(std::uint32_t(e.coordinate));ew.push_back(e.cumulative_before);}
  tileplace_snapshot::PressureSnapshot pressure(edges);auto expected=tileplace_snapshot::cost_pair(reference,changed,before,after,rr,pressure);
  auto actual=cost_pair_array(nets,2,touched.data(),touched.size(),blocks,positions,4,members,4,connections,2,lines.data(),lines.size(),entries.data(),entries.size(),routed,2,moves.data(),moves.size());
  std::vector<std::uint64_t> nw,bw(32),pw,cw,rw,mw;
  auto append_position=[](std::vector<std::uint64_t>& w,Location p){w.push_back(std::uint32_t(p.x)|(std::uint64_t(std::uint32_t(p.y))<<32));w.push_back(std::uint32_t(p.subtile)|(std::uint64_t(std::uint32_t(p.layer))<<32));};
  for(auto n:nets){nw.insert(nw.end(),{n.id,0,n.members.offset,n.members.count,n.connections.offset,n.connections.count});}
  for(unsigned i=0;i<4;++i){bw[8*i]=blocks[i].id;append_position(pw,positions[i]);}
  for(auto c:connections){cw.push_back(c.source|(std::uint64_t(c.sink)<<32));cw.push_back(c.weight);}
  for(auto c:routed){rw.push_back(c.source|(std::uint64_t(c.sink)<<32));rw.push_back(c.weight);}
  for(auto m:moves){mw.push_back(m.id);append_position(mw,m.target);}
  auto wire=tileplace_wire_costs::cost_pair_words(nw.data(),2,touched.data(),touched.size(),bw.data(),pw.data(),4,members,4,cw.data(),2,lw.data(),lines.size(),ew.data(),entries.size(),rw.data(),2,mw.data(),moves.size());
  if(wire.status||wire.reserved)return 5;
  for(unsigned i=0;i<4;++i)if(wire.before[i]!=expected.first[i]||wire.after[i]!=expected.second[i])return 6;
  if(actual.status||actual.reserved)return 1;
  for(unsigned i=0;i<4;++i)if(actual.before[i]!=expected.first[i]||actual.after[i]!=expected.second[i])return 2;
 }
 Block blocks[2]{};blocks[0].id=3;blocks[1].id=10;Location positions[]={{0,0,0,0},{2,0,0,0}};
 TrialMove moves[]={{3,{1,0,0,0}}};Connection routed[]={{3,10,UINT64_MAX}};unsigned touched=42;
 auto invalid=cost_pair_array(nullptr,0,&touched,1,blocks,positions,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,moves,1);
 auto overflow=cost_pair_array(nullptr,0,nullptr,0,blocks,positions,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,routed,1,moves,1);
 if(invalid.status!=1||overflow.status!=3)return 3;
 for(unsigned i=0;i<4;++i)if(invalid.before[i]||invalid.after[i]||overflow.before[i]||overflow.after[i])return 4;
 std::uint64_t bw[16]{},pw[4]={0,0,2,0},rw[2]={3|(10ULL<<32),UINT64_MAX},mw[3]={3,1,0};bw[0]=3;bw[8]=10;
 auto wi=tileplace_wire_costs::cost_pair_words(nullptr,0,&touched,1,bw,pw,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,mw,1);
 auto wo=tileplace_wire_costs::cost_pair_words(nullptr,0,nullptr,0,bw,pw,2,nullptr,0,nullptr,0,nullptr,0,nullptr,0,rw,1,mw,1);
 if(wi.status!=1||wo.status!=3)return 7;
 for(unsigned i=0;i<4;++i)if(wi.before[i]||wi.after[i]||wo.before[i]||wo.after[i])return 8;
 std::cout<<"2000 wire cost pairs and unknown-net/routed-overflow atomic errors pass\n";
}
