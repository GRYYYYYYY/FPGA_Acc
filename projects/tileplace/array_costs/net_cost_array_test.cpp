#include "net_cost_array.hpp"
#include "../cpp_snapshot/net_cost.hpp"
#include <random>
#include <iostream>
int main(){
 using namespace tileplace_cost_array;std::mt19937 rng(40);unsigned checked=0;
 for(unsigned fixture=0;fixture<500;++fixture){
  std::vector<Block> blocks(8);std::vector<Location> positions(8);tileplace_snapshot::Positions reference;
  for(unsigned i=0;i<8;++i){blocks[i].id=i*7+3;positions[i]={int(rng()%21)-10,int(rng()%21)-10,int(rng()%3),int(rng()%3)};auto p=positions[i];reference[blocks[i].id]={p.x,p.y,p.subtile,p.layer};}
  std::vector<tileplace_snapshot::Edge> edges;std::vector<PrefixLine> lines;std::vector<PrefixEntry> entries;
  for(int axis=0;axis<2;++axis)for(int line=-2;line<=2;++line){auto offset=entries.size();std::uint64_t total=0;
   for(int coordinate=-3;coordinate<=3;++coordinate){auto weight=rng()%100000;entries.push_back({coordinate,0,total});total+=weight;
    edges.push_back(axis==0?tileplace_snapshot::Edge{coordinate,line,coordinate+1,line,weight}:tileplace_snapshot::Edge{line,coordinate,line,coordinate+1,weight});}
   lines.push_back({axis,line,total,{offset,7}});
  }
  tileplace_snapshot::PressureSnapshot pressure(edges);tileplace_snapshot::Net net;
  std::vector<unsigned> members;std::vector<Connection> connections;
  for(unsigned i=0,n=fixture%9;i<n;++i){members.push_back(blocks[i].id);net.members.push_back(blocks[i].id);}
  if(!members.empty())for(unsigned i=0;i<12;++i){auto a=members[rng()%members.size()],b=members[rng()%members.size()];auto weight=rng()%100000;connections.push_back({a,b,weight});net.connections.push_back({a,b,weight});}
  Net record{};record.members={0,members.size()};record.connections={0,connections.size()};
  for(unsigned q=0;q<4;++q){auto candidate=reference;std::vector<TrialMove> moves;
   for(unsigned i=0;i<q;++i){Location p{int(rng()%31)-15,int(rng()%31)-15,int(rng()%3),int(rng()%3)};moves.push_back({blocks[i].id,p});candidate[blocks[i].id]={p.x,p.y,p.subtile,p.layer};}
   auto expected=tileplace_snapshot::net_cost(net,candidate,pressure);
   auto actual=net_cost_array(record,blocks.data(),positions.data(),blocks.size(),members.data(),members.size(),connections.data(),connections.size(),lines.data(),lines.size(),entries.data(),entries.size(),moves.data(),moves.size());
   if(actual.status||actual.reserved||actual.costs[0]!=expected[0]||actual.costs[1]!=expected[1]||actual.costs[2]!=expected[3])return 1;
   ++checked;
  }
 }
 unsigned faults=0;
 Block blocks[2]{};blocks[0].id=3;blocks[1].id=10;
 Location positions[2]={{0,0,0,0},{2,0,0,0}};
 unsigned members[2]={3,10};Connection connections[2]={{3,10,1},{3,10,1}};
 Net record{};record.members={0,2};record.connections={0,1};
 auto query=[&](Net n,const PrefixLine* lines=nullptr,unsigned count=0,const TrialMove* moves=nullptr,unsigned move_count=0){
  return net_cost_array(n,blocks,positions,2,members,2,connections,2,lines,count,nullptr,0,moves,move_count);
 };
 auto error=[&](NetCostResult r,unsigned status){
  if(r.status!=status||r.reserved||r.costs[0]||r.costs[1]||r.costs[2])return false;
  ++faults;return true;
 };
 auto bad=record;bad.members={UINT64_MAX,2};if(!error(query(bad),1))return 2;
 bad=record;bad.connections={1,2};if(!error(query(bad),1))return 3;
 members[1]=11;if(!error(query(record),2))return 4;members[1]=10;
 TrialMove move{11,{1,0,0,0}};if(!error(query(record,nullptr,0,&move,1),2))return 5;
 connections[0].sink=11;if(!error(query(record),2))return 6;connections[0].sink=10;
 connections[0].weight=UINT64_MAX;if(!error(query(record),3))return 7;
 connections[0].weight=UINT64_MAX/2;connections[1].weight=1;
 bad=record;bad.connections.count=2;if(!error(query(bad),3))return 8;
 connections[0].weight=1;
 PrefixLine line{0,0,0,{0,1}};if(!error(query(record,&line,1),4))return 9;
 positions[0]={INT32_MIN,INT32_MIN,0,0};positions[1]={INT32_MAX,INT32_MAX,0,0};
 auto extreme=query(record);if(extreme.status||extreme.costs[0]!=8589934590ULL||extreme.costs[1]!=8589934590ULL||extreme.costs[2]!=8589934590ULL*65536)return 10;
 std::cout<<faults<<" atomic error cases and extreme coordinates pass\n";
 std::cout<<checked<<" array network/overlay cost queries pass\n";
}
