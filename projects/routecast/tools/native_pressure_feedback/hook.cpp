#include "globals.h"
#include "vpr_context.h"
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cmath>
#include <stdexcept>
#include <cstdio>

extern "C" void original_alloc() asm("__real__Z36alloc_and_load_rr_node_route_structsv");
extern "C" void pressure_alloc() asm("__wrap__Z36alloc_and_load_rr_node_route_structsv");
extern "C" void pressure_alloc() {
    original_alloc();
    const char* path = std::getenv("ROUTECAST_PRESSURE_FILE");
    if (!path || !*path) return;
    const char* expected = std::getenv("ROUTECAST_EXPECT_GRAPH_SHA256");
    if (!expected) throw std::runtime_error("missing RouteCast expected graph binding");
    auto& route = g_vpr_ctx.mutable_routing();
    const auto& graph = g_vpr_ctx.device().rr_graph;
    std::ifstream file(path);
    std::string header, magic, digest;
    size_t count;
    if (!std::getline(file, header)) throw std::runtime_error("missing pressure header");
    std::istringstream head(header);
    std::string extra;
    if (!(head >> magic >> count >> digest) || (head >> extra) || magic != "ROUTECAST_PRESSURE_V1" || count != graph.num_nodes() || digest != expected)
        throw std::runtime_error("pressure graph identity mismatch");
    std::vector<std::pair<RRNodeId,float>> updates;
    std::vector<bool> seen(count,false);
    std::string line;
    while (std::getline(file,line)) {
        std::istringstream row(line);
        size_t id; unsigned capacity; float value;
        if (!(row >> id >> capacity >> value) || (row >> extra) || id >= count || seen[id] || !std::isfinite(value) || value < 1.0f)
            throw std::runtime_error("invalid pressure row");
        RRNodeId node(id);
        auto type = graph.node_type(node);
        if ((type != CHANX && type != CHANY) || capacity == 0 || int(capacity) != graph.node_capacity(node) || route.rr_node_route_inf[node].acc_cost != 1.0f)
            throw std::runtime_error("pressure capacity/type/initial state mismatch");
        seen[id]=true; updates.emplace_back(node,value);
    }
    if (!file.eof()) throw std::runtime_error("pressure read failure");
    // Validate the complete payload before changing any node cost.
    for (const auto& update : updates) route.rr_node_route_inf[update.first].acc_cost=update.second;
    std::fprintf(stderr,"RouteCast pressure applied: %zu channel nodes, graph %s\n",updates.size(),digest.c_str());
}
