#include "fpga_acc/router.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <future>
#include <iomanip>
#include <limits>
#include <numeric>
#include <queue>
#include <random>
#include <sstream>
#include <stdexcept>
#include <tuple>
#include <unordered_set>

namespace fpga_acc {
namespace {

using Clock = std::chrono::steady_clock;

struct SearchResult {
    RouteTransaction transaction;
    std::uint64_t nodes_expanded = 0;
    std::uint64_t edges_examined = 0;
};

struct QueueEntry {
    double total_cost = 0.0;
    double path_cost = 0.0;
    std::uint32_t node = 0;
    std::uint32_t predecessor = kInvalidId;
};

struct QueueGreater {
    bool operator()(const QueueEntry& lhs, const QueueEntry& rhs) const {
        return std::tie(lhs.total_cost, lhs.path_cost, lhs.node, lhs.predecessor) >
               std::tie(rhs.total_cost, rhs.path_cost, rhs.node, rhs.predecessor);
    }
};

double milliseconds(Clock::time_point begin, Clock::time_point end) {
    return std::chrono::duration<double, std::milli>(end - begin).count();
}

double criticality(const ConnectionTask& task) {
    return static_cast<double>(task.criticality_q) / 65535.0;
}

double heuristic(const GridRoutingGraph& graph, std::uint32_t a, std::uint32_t b) {
    return static_cast<double>(
        std::abs(static_cast<int>(graph.x(a)) - static_cast<int>(graph.x(b))) +
        std::abs(static_cast<int>(graph.y(a)) - static_cast<int>(graph.y(b))));
}

bool in_bbox(const GridRoutingGraph& graph, const ConnectionTask& task, std::uint32_t n) {
    const auto nx = graph.x(n);
    const auto ny = graph.y(n);
    return nx >= task.bbox_xmin && nx <= task.bbox_xmax &&
           ny >= task.bbox_ymin && ny <= task.bbox_ymax;
}

SearchResult search_connection(
    const GridRoutingGraph& graph,
    const std::vector<ResourceState>& resources,
    const Connection& connection,
    double present_factor) {
    const auto& task = connection.task;
    const auto count = graph.node_count();
    const double infinity = std::numeric_limits<double>::infinity();
    std::vector<double> distance(count, infinity);
    std::vector<std::uint32_t> predecessor(count, kInvalidId);
    std::vector<std::uint8_t> read_mask(count, 0);
    std::priority_queue<QueueEntry, std::vector<QueueEntry>, QueueGreater> queue;

    distance[task.source_node] = 0.0;
    queue.push({heuristic(graph, task.source_node, task.sink_node), 0.0,
                task.source_node, kInvalidId});

    SearchResult output;
    output.transaction.connection_id = task.connection_id;
    output.transaction.epoch = task.epoch;
    output.transaction.priority = task.priority;

    while (!queue.empty()) {
        const QueueEntry current = queue.top();
        queue.pop();
        if (current.path_cost != distance[current.node]) {
            continue;
        }
        ++output.nodes_expanded;
        if (current.node == task.sink_node) {
            break;
        }

        for (const auto next : graph.neighbors(current.node)) {
            ++output.edges_examined;
            if (!in_bbox(graph, task, next)) {
                continue;
            }
            const auto& state = resources[next];
            read_mask[next] = 1;
            const double occ_ratio = static_cast<double>(state.occupancy) /
                                     std::max<std::uint16_t>(1, state.capacity);
            const double congestion = 1.0 +
                present_factor * occ_ratio +
                static_cast<double>(state.history_cost_q) / 256.0;
            const double step = criticality(task) +
                (1.0 - criticality(task)) * congestion;
            const double candidate = current.path_cost + step;
            if (candidate < distance[next] ||
                (candidate == distance[next] && current.node < predecessor[next])) {
                distance[next] = candidate;
                predecessor[next] = current.node;
                queue.push({candidate + heuristic(graph, next, task.sink_node),
                            candidate, next, current.node});
            }
        }
    }

    if (!std::isfinite(distance[task.sink_node])) {
        output.transaction.status = TransactionStatus::Failed;
        return output;
    }

    std::vector<std::uint32_t> reverse_path;
    for (std::uint32_t n = task.sink_node; n != kInvalidId; n = predecessor[n]) {
        reverse_path.push_back(n);
        if (n == task.source_node) {
            break;
        }
    }
    if (reverse_path.empty() || reverse_path.back() != task.source_node) {
        output.transaction.status = TransactionStatus::Failed;
        return output;
    }
    output.transaction.candidate_path.assign(reverse_path.rbegin(), reverse_path.rend());

    std::unordered_set<std::uint32_t> old_route(connection.route.begin(), connection.route.end());
    std::unordered_set<std::uint32_t> new_route(
        output.transaction.candidate_path.begin(), output.transaction.candidate_path.end());
    for (const auto resource_id : old_route) read_mask[resource_id] = 1;
    for (const auto resource_id : new_route) read_mask[resource_id] = 1;

    output.transaction.read_set.reserve(output.nodes_expanded * 2);
    for (std::uint32_t resource_id = 0; resource_id < count; ++resource_id) {
        if (read_mask[resource_id] != 0) {
            output.transaction.read_set.push_back({resource_id, resources[resource_id].version});
        }
    }

    for (const auto resource_id : old_route) {
        if (new_route.count(resource_id) == 0) {
            output.transaction.write_set.push_back({resource_id, -1, 0});
        }
    }
    for (const auto resource_id : new_route) {
        if (old_route.count(resource_id) == 0) {
            output.transaction.write_set.push_back({resource_id, 1, 0});
        }
    }
    std::sort(output.transaction.write_set.begin(), output.transaction.write_set.end(),
              [](const auto& a, const auto& b) { return a.resource_id < b.resource_id; });
    return output;
}

bool commit_transaction(
    RouteTransaction& transaction,
    std::vector<ResourceState>& resources,
    std::vector<Connection>& connections) {
    for (const auto& read : transaction.read_set) {
        if (resources[read.resource_id].version != read.observed_version) {
            transaction.status = TransactionStatus::Conflict;
            return false;
        }
    }

    for (const auto& write : transaction.write_set) {
        const auto& state = resources[write.resource_id];
        const int next = static_cast<int>(state.occupancy) + write.delta_occupancy;
        if (next < 0 || next > std::numeric_limits<std::uint16_t>::max()) {
            transaction.status = TransactionStatus::Failed;
            return false;
        }
    }

    for (const auto& write : transaction.write_set) {
        auto& state = resources[write.resource_id];
        state.occupancy = static_cast<std::uint16_t>(
            static_cast<int>(state.occupancy) + write.delta_occupancy);
        ++state.version;
    }
    connections.at(transaction.connection_id).route = transaction.candidate_path;
    transaction.status = TransactionStatus::Committed;
    return true;
}

void remove_route(Connection& connection, std::vector<ResourceState>& resources) {
    for (const auto node : connection.route) {
        auto& state = resources[node];
        if (state.occupancy == 0) {
            throw std::logic_error("route/resource occupancy mismatch");
        }
        --state.occupancy;
        ++state.version;
    }
    connection.route.clear();
}

std::uint64_t fnv1a(std::uint64_t hash, std::uint32_t value) {
    for (int byte = 0; byte < 4; ++byte) {
        hash ^= static_cast<std::uint8_t>((value >> (byte * 8)) & 0xffU);
        hash *= 1099511628211ULL;
    }
    return hash;
}

void update_costs(std::vector<ResourceState>& resources, const RouterConfig& config) {
    for (auto& state : resources) {
        const auto overuse = state.occupancy > state.capacity
            ? static_cast<std::uint32_t>(state.occupancy - state.capacity)
            : 0U;
        const double present = 1.0 + config.present_factor * overuse;
        state.present_cost_q = static_cast<std::uint16_t>(
            std::min(65535.0, std::round(present * 256.0)));
        if (overuse != 0) {
            const double next_history = static_cast<double>(state.history_cost_q) +
                                        config.history_increment * 256.0 * overuse;
            state.history_cost_q = static_cast<std::uint16_t>(
                std::min(65535.0, std::round(next_history)));
        }
    }
}

std::uint64_t count_overused(const std::vector<ResourceState>& resources) {
    return static_cast<std::uint64_t>(std::count_if(
        resources.begin(), resources.end(),
        [](const auto& state) { return state.occupancy > state.capacity; }));
}

bool validate_result(const GridRoutingGraph& graph, const RouterResult& result) {
    std::vector<std::uint32_t> observed(graph.node_count(), 0);
    for (const auto& connection : result.connections) {
        if (connection.route.empty() ||
            connection.route.front() != connection.task.source_node ||
            connection.route.back() != connection.task.sink_node) {
            return false;
        }
        for (std::size_t i = 0; i < connection.route.size(); ++i) {
            const auto node = connection.route[i];
            if (node >= graph.node_count()) {
                return false;
            }
            ++observed[node];
            if (i != 0) {
                const auto neighbors = graph.neighbors(connection.route[i - 1]);
                if (std::find(neighbors.begin(), neighbors.end(), node) == neighbors.end()) {
                    return false;
                }
            }
        }
    }
    for (std::size_t i = 0; i < observed.size(); ++i) {
        if (observed[i] != result.resources[i].occupancy ||
            observed[i] > result.resources[i].capacity) {
            return false;
        }
    }
    return true;
}

}  // namespace

GridRoutingGraph::GridRoutingGraph(
    std::uint32_t width, std::uint32_t height, std::uint16_t capacity)
    : width_(width), height_(height), initial_state_(width * height) {
    if (width < 2 || height < 2 || capacity == 0) {
        throw std::invalid_argument("grid dimensions must be >=2 and capacity must be >0");
    }
    for (auto& state : initial_state_) {
        state.capacity = capacity;
    }
}

std::vector<std::uint32_t> GridRoutingGraph::neighbors(std::uint32_t node_id) const {
    if (node_id >= node_count()) {
        throw std::out_of_range("node id outside graph");
    }
    const auto nx = x(node_id);
    const auto ny = y(node_id);
    std::vector<std::uint32_t> output;
    output.reserve(4);
    if (nx > 0) output.push_back(node(nx - 1, ny));
    if (ny > 0) output.push_back(node(nx, ny - 1));
    if (nx + 1 < width_) output.push_back(node(nx + 1, ny));
    if (ny + 1 < height_) output.push_back(node(nx, ny + 1));
    std::sort(output.begin(), output.end());
    return output;
}

std::vector<Connection> make_synthetic_connections(
    const GridRoutingGraph& graph,
    std::uint32_t count,
    std::uint32_t seed,
    const std::string& pattern,
    std::uint32_t bbox_margin) {
    std::mt19937 generator(seed);
    std::uniform_int_distribution<std::uint32_t> x_dist(0, graph.width() - 1);
    std::uniform_int_distribution<std::uint32_t> y_dist(0, graph.height() - 1);
    std::vector<Connection> connections;
    connections.reserve(count);

    for (std::uint32_t id = 0; id < count; ++id) {
        std::uint32_t sx = x_dist(generator);
        std::uint32_t sy = y_dist(generator);
        std::uint32_t tx = x_dist(generator);
        std::uint32_t ty = y_dist(generator);
        if (pattern == "cross") {
            const bool horizontal = (id % 2) == 0;
            if (horizontal) {
                sx = 0;
                tx = graph.width() - 1;
                sy = ty = static_cast<std::uint32_t>((id * 3U + seed) % graph.height());
            } else {
                sy = 0;
                ty = graph.height() - 1;
                sx = tx = static_cast<std::uint32_t>((id * 5U + seed) % graph.width());
            }
        } else if (pattern == "hotspot") {
            tx = graph.width() / 2 + static_cast<std::uint32_t>(id % 3) - 1;
            ty = graph.height() / 2 + static_cast<std::uint32_t>((id / 3) % 3) - 1;
        } else if (pattern != "random") {
            throw std::invalid_argument("pattern must be random, cross, or hotspot");
        }
        if (sx == tx && sy == ty) {
            tx = (tx + 1) % graph.width();
        }

        Connection connection;
        auto& task = connection.task;
        task.connection_id = id;
        task.net_id = id;
        task.source_node = graph.node(sx, sy);
        task.sink_node = graph.node(tx, ty);
        const auto min_x = std::min(sx, tx);
        const auto min_y = std::min(sy, ty);
        task.bbox_xmin = static_cast<std::uint16_t>(min_x > bbox_margin ? min_x - bbox_margin : 0);
        task.bbox_ymin = static_cast<std::uint16_t>(min_y > bbox_margin ? min_y - bbox_margin : 0);
        task.bbox_xmax = static_cast<std::uint16_t>(std::min(graph.width() - 1, std::max(sx, tx) + bbox_margin));
        task.bbox_ymax = static_cast<std::uint16_t>(std::min(graph.height() - 1, std::max(sy, ty) + bbox_margin));
        task.criticality_q = static_cast<std::uint16_t>((id * 7919U + seed) % 65536U);
        task.epoch = 0;
        task.priority = id;
        task.footprint_id = (task.bbox_xmin / 4U) | ((task.bbox_ymin / 4U) << 16U);
        task.seed_or_tie = id;
        connections.push_back(std::move(connection));
    }
    return connections;
}

RouterResult route_connections(
    const GridRoutingGraph& graph,
    std::vector<Connection> connections,
    const RouterConfig& config) {
    if (config.batch_size == 0 || config.worker_threads == 0 || config.max_iterations == 0) {
        throw std::invalid_argument("router configuration values must be positive");
    }
    RouterResult result;
    result.connections = std::move(connections);
    result.resources = graph.initial_state();
    const auto wall_begin = Clock::now();

    for (std::uint32_t iteration = 0; iteration < config.max_iterations; ++iteration) {
        result.metrics.iterations = iteration + 1;
        for (auto& connection : result.connections) {
            connection.task.epoch = iteration;
        }

        const std::size_t execution_width = config.speculative
            ? std::min<std::uint32_t>(config.batch_size, config.worker_threads)
            : 1U;
        for (std::size_t begin = 0; begin < result.connections.size(); begin += execution_width) {
            const std::size_t end = std::min(result.connections.size(), begin + execution_width);
            std::vector<SearchResult> searches;
            searches.reserve(end - begin);
            const auto search_begin = Clock::now();

            if (config.speculative && execution_width > 1 && end - begin > 1) {
                std::vector<std::future<SearchResult>> futures;
                futures.reserve(end - begin);
                for (std::size_t i = begin; i < end; ++i) {
                    futures.push_back(std::async(std::launch::async, [&, i]() {
                        return search_connection(graph, result.resources,
                                                 result.connections[i], config.present_factor);
                    }));
                }
                for (auto& future : futures) searches.push_back(future.get());
            } else {
                for (std::size_t i = begin; i < end; ++i) {
                    searches.push_back(search_connection(
                        graph, result.resources, result.connections[i], config.present_factor));
                }
            }
            result.metrics.search_ms += milliseconds(search_begin, Clock::now());

            std::sort(searches.begin(), searches.end(), [](const auto& a, const auto& b) {
                return std::tie(a.transaction.epoch, a.transaction.priority,
                                a.transaction.connection_id) <
                       std::tie(b.transaction.epoch, b.transaction.priority,
                                b.transaction.connection_id);
            });
            const auto commit_begin = Clock::now();
            for (auto& search : searches) {
                ++result.metrics.searches;
                result.metrics.nodes_expanded += search.nodes_expanded;
                result.metrics.edges_examined += search.edges_examined;
                if (search.transaction.status == TransactionStatus::Failed) {
                    ++result.metrics.failed_searches;
                    continue;
                }
                if (commit_transaction(search.transaction, result.resources, result.connections)) {
                    ++result.metrics.commits;
                    continue;
                }
                ++result.metrics.conflicts;
                ++result.metrics.replays;
                const auto id = search.transaction.connection_id;
                auto replay = search_connection(
                    graph, result.resources, result.connections[id], config.present_factor);
                ++result.metrics.searches;
                result.metrics.nodes_expanded += replay.nodes_expanded;
                result.metrics.edges_examined += replay.edges_examined;
                if (replay.transaction.status == TransactionStatus::Failed ||
                    !commit_transaction(replay.transaction, result.resources, result.connections)) {
                    ++result.metrics.failed_searches;
                } else {
                    ++result.metrics.commits;
                }
            }
            result.metrics.commit_ms += milliseconds(commit_begin, Clock::now());
        }

        const auto overused = count_overused(result.resources);
        result.metrics.overused_resources = overused;
        if (overused == 0 && std::all_of(result.connections.begin(), result.connections.end(),
                                        [](const auto& c) { return !c.route.empty(); })) {
            result.route_success = true;
            break;
        }

        update_costs(result.resources, config);
        std::vector<std::uint32_t> reroute_ids;
        for (const auto& connection : result.connections) {
            const bool touches_overuse = std::any_of(
                connection.route.begin(), connection.route.end(),
                [&](const auto n) { return result.resources[n].occupancy > result.resources[n].capacity; });
            if (connection.route.empty() || touches_overuse) reroute_ids.push_back(connection.task.connection_id);
        }
        for (const auto id : reroute_ids) remove_route(result.connections[id], result.resources);
    }

    result.total_wirelength = 0;
    result.route_hash = 1469598103934665603ULL;
    for (const auto& connection : result.connections) {
        if (!connection.route.empty()) result.total_wirelength += connection.route.size() - 1;
        result.route_hash = fnv1a(result.route_hash, connection.task.connection_id);
        for (const auto node : connection.route) result.route_hash = fnv1a(result.route_hash, node);
    }
    result.metrics.wall_ms = milliseconds(wall_begin, Clock::now());
    result.legal = result.route_success && validate_result(graph, result);
    return result;
}

std::string result_to_json(
    const RouterResult& result,
    const GridRoutingGraph& graph,
    const RouterConfig& config,
    const std::string& pattern,
    std::uint32_t seed) {
    const auto& m = result.metrics;
    std::ostringstream out;
    out << std::fixed << std::setprecision(6);
    out << "{\n"
        << "  \"schema_version\": 1,\n"
        << "  \"design\": {\"width\": " << graph.width()
        << ", \"height\": " << graph.height()
        << ", \"connections\": " << result.connections.size()
        << ", \"pattern\": \"" << pattern << "\", \"seed\": " << seed << "},\n"
        << "  \"config\": {\"max_iterations\": " << config.max_iterations
        << ", \"batch_size\": " << config.batch_size
        << ", \"worker_threads\": " << config.worker_threads
        << ", \"speculative\": " << (config.speculative ? "true" : "false") << "},\n"
        << "  \"result\": {\"legal\": " << (result.legal ? "true" : "false")
        << ", \"route_success\": " << (result.route_success ? "true" : "false")
        << ", \"wirelength\": " << result.total_wirelength
        << ", \"route_hash\": \"" << std::hex << result.route_hash << std::dec << "\"},\n"
        << "  \"metrics\": {\"iterations\": " << m.iterations
        << ", \"searches\": " << m.searches
        << ", \"nodes_expanded\": " << m.nodes_expanded
        << ", \"edges_examined\": " << m.edges_examined
        << ", \"commits\": " << m.commits
        << ", \"conflicts\": " << m.conflicts
        << ", \"replays\": " << m.replays
        << ", \"failed_searches\": " << m.failed_searches
        << ", \"overused_resources\": " << m.overused_resources
        << ", \"search_ms\": " << m.search_ms
        << ", \"commit_ms\": " << m.commit_ms
        << ", \"wall_ms\": " << m.wall_ms << "}\n"
        << "}\n";
    return out.str();
}

}  // namespace fpga_acc
