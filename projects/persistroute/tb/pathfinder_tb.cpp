#include "pathfinder.hpp"

#include <algorithm>
#include <cassert>
#include <iostream>
#include <tuple>
#include <vector>

using namespace persistroute;

namespace {

struct Arc {std::uint32_t src, dst;std::uint16_t cost, delay;};

void make_graph(
 std::uint32_t node_count,
 std::vector<Arc> arcs,
 std::vector<Node>& nodes,
 std::vector<Edge>& edges) {
 std::sort(arcs.begin(), arcs.end(), [](const Arc& a, const Arc& b) {
  return std::tie(a.src, a.dst, a.cost, a.delay) < std::tie(b.src, b.dst, b.cost, b.delay);
 });
 nodes.assign(node_count, Node{});
 edges.clear();
 std::size_t cursor = 0;
 for (std::uint32_t node = 0; node < node_count; ++node) {
  nodes[node].edge_begin = static_cast<std::uint32_t>(edges.size());
  while (cursor < arcs.size() && arcs[cursor].src == node) {
   edges.push_back({arcs[cursor].dst, arcs[cursor].cost, arcs[cursor].delay});
   ++nodes[node].edge_count;
   ++cursor;
  }
 }
 assert(cursor == arcs.size());
}

std::vector<Resource> resources(std::size_t count) {
 return std::vector<Resource>(count, Resource{0,1,0,0,0,INVALID_RESOURCE});
}

void test_route_tree_trunk_sharing() {
 std::vector<Node> nodes;std::vector<Edge> edges;
 make_graph(4,{{0,1,1,0},{1,2,1,0},{1,3,1,0}},nodes,edges);
 const std::vector<Task> tasks{
  {1,7,0,2,0,8,0,0,0},
  {2,7,0,3,0,8,1,0,0},
 };
 const auto initial=resources(4);const auto result=route_pathfinder(nodes,edges,initial,tasks);
 assert(result.legal&&result.metrics.iterations==1&&result.route_trees.size()==1);
 assert((result.tasks[0].path==std::vector<std::uint32_t>{1,2}));
 assert((result.tasks[1].path==std::vector<std::uint32_t>{1,3}));
 assert(result.resources[1].occupancy==1&&result.resources[1].owner==7);
 assert(result.route_trees[0].nodes.size()==4&&result.route_trees[0].edges.size()==3);
}

PathfinderResult run_negotiated_case() {
 std::vector<Node> nodes;std::vector<Edge> edges;
 make_graph(8,{
  {0,1,1,0},{0,2,1000,0},{1,3,1,0},{1,5,1,0},
  {2,3,1000,0},{2,5,300,0},{4,1,1,0},{4,2,300,0},{6,7,1,0},
 },nodes,edges);
 const std::vector<Task> tasks{
  {10,10,0,3,0,8,0,0,0},
  {20,20,4,5,0,8,1,0,0},
  {30,30,6,7,0,8,2,0,0},
 };
 PathfinderConfig config;config.max_iterations=5;
 return route_pathfinder(nodes,edges,resources(8),tasks,config);
}

void test_negotiated_congestion_and_determinism() {
 const auto first=run_negotiated_case();const auto second=run_negotiated_case();
 assert(first.legal&&first.metrics.iterations==2&&first.metrics.ripups==2);
 assert(first.iteration_log.size()==2&&first.iteration_log[0].overused_resources==1);
 assert(first.iteration_log[1].overused_resources==0);
 assert((first.tasks[0].path==std::vector<std::uint32_t>{1,3}));
 assert((first.tasks[1].path==std::vector<std::uint32_t>{2,5}));
 assert((first.tasks[2].path==std::vector<std::uint32_t>{7}));
 assert(first.tasks[2].task.epoch==0&&first.metrics.searches==5);
 assert(first.resources[1].history_cost_q>0);
 assert(first.tasks[0].path==second.tasks[0].path&&first.tasks[1].path==second.tasks[1].path);
 assert(first.metrics.searches==second.metrics.searches&&
        first.metrics.edge_visits==second.metrics.edge_visits);
}

void test_impossible_case_remains_illegal() {
 std::vector<Node> nodes;std::vector<Edge> edges;
 make_graph(5,{{0,1,1,0},{1,2,1,0},{1,4,1,0},{3,1,1,0}},nodes,edges);
 const std::vector<Task> tasks{
  {1,1,0,2,0,8,0,0,0},
  {2,2,3,4,0,8,1,0,0},
 };
 PathfinderConfig config;config.max_iterations=3;
 const auto result=route_pathfinder(nodes,edges,resources(5),tasks,config);
 assert(!result.route_success&&!result.legal&&result.metrics.iterations==3);
 assert(result.metrics.overused_resources==1&&result.resources[1].history_cost_q>0);
}

void test_periodic_timing_updates() {
 std::vector<Node> nodes;std::vector<Edge> edges;
 make_graph(5,{{0,1,1,10},{1,2,1,20},{3,1,1,10},{1,4,1,20}},nodes,edges);
 const std::vector<Task> tasks{{1,1,0,2,0,8,0,0,0},{2,2,3,4,0,8,1,0,0}};
 PathfinderConfig config;config.max_iterations=3;
 std::vector<std::vector<std::uint16_t>> observed;
 TimingAnalyzer analyzer=[&](std::uint32_t iteration,const auto&,const auto&,const auto& routed){
  observed.push_back({routed[0].task.criticality_q,routed[1].task.criticality_q});
  TimingAnalysisResult out;out.critical_path_delay_ps=1000+iteration;
  out.connections={{1,static_cast<std::uint16_t>(10000+iteration),30,-100},
                   {2,static_cast<std::uint16_t>(50000+iteration),30,-200}};
  return out;
 };
 const auto result=route_pathfinder(nodes,edges,resources(5),tasks,config,analyzer);
 assert(!result.legal&&result.timing_log.size()==3&&observed.size()==3);
 assert((observed[0]==std::vector<std::uint16_t>{0,0}));
 assert((observed[1]==std::vector<std::uint16_t>{10000,50000}));
 assert(result.tasks[0].task.criticality_q==10002&&result.tasks[1].task.criticality_q==50002);
 assert(result.timing_log[0].updated_connections==2&&result.timing_log[2].critical_path_delay_ps==1002);
}

void test_timing_feedback_forces_reroute() {
 std::vector<Node> nodes;std::vector<Edge> edges;
 make_graph(3,{{0,1,1,100},{0,2,10,1},{2,1,10,1}},nodes,edges);
 const std::vector<Task> tasks{{1,1,0,1,0,8,0,0,0}};
 PathfinderConfig config;config.max_iterations=4;config.min_timing_iterations=3;
 std::uint32_t calls=0;
 TimingAnalyzer analyzer=[&](std::uint32_t iteration,const auto&,const auto&,const auto&){
  ++calls;TimingAnalysisResult out;out.critical_path_delay_ps=100-iteration;
  out.connections={{1,65535,0,0}};return out;
 };
 const auto result=route_pathfinder(nodes,edges,resources(3),tasks,config,analyzer);
 assert(result.legal&&result.metrics.iterations==3&&calls==3&&result.metrics.ripups==2);
 assert((result.tasks[0].path==std::vector<std::uint32_t>{2,1}));
}

void test_timing_feedback_reorders_nets() {
 std::vector<Node> nodes;std::vector<Edge> edges;
 make_graph(6,{{0,1,1,1},{0,2,10,100},{1,3,1,1},{2,3,10,100},
               {4,1,1,1},{4,2,10,100},{1,5,1,1},{2,5,10,100}},nodes,edges);
 const std::vector<Task> tasks{{1,1,4,5,0,8,0,0,0},{2,2,0,3,0,8,1,0,0}};
 PathfinderConfig config;config.max_iterations=3;config.min_timing_iterations=2;
 TimingAnalyzer analyzer=[](std::uint32_t,const auto&,const auto&,const auto&){
  TimingAnalysisResult out;out.connections={{1,0,0,0},{2,65535,0,0}};return out;
 };
 const auto result=route_pathfinder(nodes,edges,resources(6),tasks,config,analyzer);
 assert(result.legal&&result.metrics.iterations==2);
 assert((result.tasks[0].path==std::vector<std::uint32_t>{2,5}));
 assert((result.tasks[1].path==std::vector<std::uint32_t>{1,3}));
}

} // namespace

int main() {
 test_route_tree_trunk_sharing();
 test_negotiated_congestion_and_determinism();
 test_impossible_case_remains_illegal();
 test_periodic_timing_updates();
 test_timing_feedback_forces_reroute();
 test_timing_feedback_reorders_nets();
 std::cout<<"pathfinder_tb: PASS\n";
}
