#pragma once

#include "fpga_acc/schema.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace fpga_acc {

class GridRoutingGraph {
public:
    GridRoutingGraph(std::uint32_t width, std::uint32_t height, std::uint16_t capacity);

    std::uint32_t width() const { return width_; }
    std::uint32_t height() const { return height_; }
    std::uint32_t node_count() const { return width_ * height_; }
    std::uint32_t node(std::uint32_t x, std::uint32_t y) const { return y * width_ + x; }
    std::uint32_t x(std::uint32_t node_id) const { return node_id % width_; }
    std::uint32_t y(std::uint32_t node_id) const { return node_id / width_; }
    std::vector<std::uint32_t> neighbors(std::uint32_t node_id) const;
    const std::vector<ResourceState>& initial_state() const { return initial_state_; }

private:
    std::uint32_t width_;
    std::uint32_t height_;
    std::vector<ResourceState> initial_state_;
};

struct Connection {
    ConnectionTask task;
    std::vector<std::uint32_t> route;
};

struct RouterConfig {
    std::uint32_t max_iterations = 30;
    std::uint32_t batch_size = 1;
    std::uint32_t worker_threads = 1;
    std::uint32_t bbox_margin = 4;
    double present_factor = 2.0;
    double history_increment = 1.0;
    bool speculative = false;
};

struct RouterMetrics {
    std::uint64_t searches = 0;
    std::uint64_t nodes_expanded = 0;
    std::uint64_t edges_examined = 0;
    std::uint64_t commits = 0;
    std::uint64_t conflicts = 0;
    std::uint64_t replays = 0;
    std::uint64_t failed_searches = 0;
    std::uint64_t overused_resources = 0;
    std::uint32_t iterations = 0;
    double search_ms = 0.0;
    double commit_ms = 0.0;
    double wall_ms = 0.0;
};

struct RouterResult {
    bool legal = false;
    bool route_success = false;
    std::uint64_t total_wirelength = 0;
    std::uint64_t route_hash = 0;
    RouterMetrics metrics;
    std::vector<Connection> connections;
    std::vector<ResourceState> resources;
};

std::vector<Connection> make_synthetic_connections(
    const GridRoutingGraph& graph,
    std::uint32_t count,
    std::uint32_t seed,
    const std::string& pattern,
    std::uint32_t bbox_margin);

RouterResult route_connections(
    const GridRoutingGraph& graph,
    std::vector<Connection> connections,
    const RouterConfig& config);

std::string result_to_json(
    const RouterResult& result,
    const GridRoutingGraph& graph,
    const RouterConfig& config,
    const std::string& pattern,
    std::uint32_t seed);

}  // namespace fpga_acc
