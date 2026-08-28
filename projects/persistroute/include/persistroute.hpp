#pragma once
#include <cstdint>
#include "multiqueue.hpp"
namespace persistroute {
constexpr std::uint32_t MAX_RESOURCES=8192,MAX_EDGES=65536,MAX_TASKS=1024,MAX_PATH=256,MAX_TX_ENTRIES=4096;
struct Node {std::uint32_t edge_begin;std::uint16_t edge_count;std::uint16_t delay_class;};
struct Edge {std::uint32_t dst;std::uint16_t base_cost_q;std::uint16_t delay_q;};
struct Resource {std::uint16_t occupancy,capacity,present_cost_q,history_cost_q;std::uint32_t version;std::uint32_t owner;};
struct Task {std::uint32_t id,net_id,source,sink;std::uint16_t criticality_q,max_hops;std::uint32_t priority,epoch,reserved;};
struct PathResult {std::uint32_t offset;std::uint16_t length,status;std::uint32_t read_offset;std::uint16_t read_count,reserved;};
struct ReadEntry {std::uint32_t resource_id,version;};
struct Metrics {std::uint64_t expanded,edge_visits,commits,conflicts,failed;};
extern "C" void search_kernel(const Node nodes[MAX_RESOURCES],const Edge edges[MAX_EDGES],const Resource resources[MAX_RESOURCES],const Task tasks[MAX_TASKS],std::uint32_t path_pool[MAX_TX_ENTRIES],ReadEntry read_pool[MAX_TX_ENTRIES],PathResult results[MAX_TASKS],std::uint32_t node_count,std::uint32_t edge_count,std::uint32_t task_count,Metrics* metrics);
extern "C" void search_hbm_kernel(const Node* nodes,const Edge* edges,const Resource* resources,const Task* tasks,std::uint32_t* path_pool,ReadEntry* read_pool,PathResult* results,std::uint32_t* distance,std::uint32_t* predecessor,std::uint32_t* hop_count,std::uint32_t* seen_epoch,std::uint32_t* closed_epoch,std::uint32_t* read_epoch,MQEntry* queue_data,std::uint32_t* queue_sizes,std::uint32_t node_count,std::uint32_t edge_count,std::uint32_t task_count,std::uint32_t queue_depth,std::uint32_t transaction_capacity,Metrics* metrics);
extern "C" void commit_kernel(Resource resources[MAX_RESOURCES],const Task tasks[MAX_TASKS],const std::uint32_t path_pool[MAX_TX_ENTRIES],const ReadEntry read_pool[MAX_TX_ENTRIES],PathResult results[MAX_TASKS],std::uint32_t resource_count,std::uint32_t task_count,Metrics* metrics);
extern "C" void commit_hbm_kernel(Resource* resources0,Resource* resources1,Resource* resources2,Resource* resources3,const Task* tasks,const std::uint32_t* path_pool,const ReadEntry* read_pool,PathResult* results,std::uint32_t resource_count,std::uint32_t task_count,std::uint32_t transaction_capacity,std::uint32_t allow_overuse,Metrics* metrics);
}
