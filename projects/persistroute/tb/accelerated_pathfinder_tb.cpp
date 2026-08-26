#include "accelerated_pathfinder.hpp"

#include <algorithm>
#include <cassert>
#include <iostream>
#include <tuple>
#include <vector>

using namespace persistroute;
namespace {
struct Arc {std::uint32_t src,dst;std::uint16_t cost;};
void graph(std::uint32_t count,std::vector<Arc> arcs,std::vector<Node>& nodes,std::vector<Edge>& edges){
 std::sort(arcs.begin(),arcs.end(),[](const auto& a,const auto& b){return std::tie(a.src,a.dst,a.cost)<std::tie(b.src,b.dst,b.cost);});nodes.assign(count,{});edges.clear();std::size_t cursor=0;
 for(std::uint32_t node=0;node<count;++node){nodes[node].edge_begin=edges.size();while(cursor<arcs.size()&&arcs[cursor].src==node){edges.push_back({arcs[cursor].dst,arcs[cursor].cost,0});++nodes[node].edge_count;++cursor;}}
}
std::vector<Resource> state(std::size_t count){return std::vector<Resource>(count,{0,1,0,0,0,INVALID_RESOURCE});}
AcceleratedPathfinderResult run(){
 std::vector<Node> nodes;std::vector<Edge> edges;graph(8,{{0,1,1},{0,2,1000},{1,3,1},{1,5,1},{2,3,1000},{2,5,300},{4,1,1},{4,2,300},{6,7,1}},nodes,edges);
 std::vector<Task> tasks{{10,10,0,3,0,8,0,0,0},{20,20,4,5,0,8,1,0,0},{30,30,6,7,0,8,2,0,0}};PathfinderConfig config;config.max_iterations=5;
 KernelBatchExecutor executor=[](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over){return execute_hbm_cmodel_batch(n,e,r,t,s,over,4);};
 return route_accelerated_pathfinder(nodes,edges,state(nodes.size()),tasks,executor,config);
}
}
int main(){
 const auto first=run(),second=run();
 assert(first.routing.legal&&first.routing.metrics.iterations>1);assert(first.audit.front().overused_resources==1&&first.audit.back().overused_resources==0);assert(first.audit.size()==second.audit.size());
 for(std::size_t i=0;i<first.audit.size();++i)assert(first.audit[i].resource_hash==second.audit[i].resource_hash&&first.audit[i].route_hash==second.audit[i].route_hash);
 std::vector<Node> nodes;std::vector<Edge> edges;graph(4,{{0,1,1},{1,2,1},{1,3,1}},nodes,edges);std::vector<Task> tasks{{1,7,0,2,0,8,0,0,0},{2,7,0,3,0,8,1,0,0}};
 KernelBatchExecutor executor=[](const auto& n,const auto& e,auto& r,const auto& t,const auto& s,bool over){return execute_hbm_cmodel_batch(n,e,r,t,s,over,4);};const auto shared=route_accelerated_pathfinder(nodes,edges,state(4),tasks,executor);
 assert(shared.routing.legal&&shared.routing.resources[1].occupancy==1&&shared.routing.route_trees[0].edges.size()==3);
 std::cout<<"accelerated_pathfinder_tb: PASS\n";
}
