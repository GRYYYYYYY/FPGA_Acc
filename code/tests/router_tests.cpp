#include "fpga_acc/router.hpp"
#include "fpga_acc/schema.hpp"

#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

fpga_acc::RouterResult run(
    const fpga_acc::GridRoutingGraph& graph,
    const std::string& pattern,
    std::uint32_t seed,
    bool speculative) {
    auto connections = fpga_acc::make_synthetic_connections(graph, 12, seed, pattern, 5);
    fpga_acc::RouterConfig config;
    config.max_iterations = 20;
    config.batch_size = speculative ? 4 : 1;
    config.worker_threads = speculative ? 4 : 1;
    config.speculative = speculative;
    return fpga_acc::route_connections(graph, std::move(connections), config);
}

}  // namespace

int main() {
    try {
        require(sizeof(fpga_acc::FileHeader) == 64, "FileHeader layout");
        require(sizeof(fpga_acc::ConnectionTask) == 64, "ConnectionTask layout");
        require(sizeof(fpga_acc::ResourceState) == 16, "ResourceState layout");
        require(sizeof(fpga_acc::TimingSnapshot) == 16, "TimingSnapshot layout");

        const fpga_acc::GridRoutingGraph graph(16, 16, 3);
        require(graph.neighbors(graph.node(0, 0)).size() == 2, "corner degree");
        require(graph.neighbors(graph.node(8, 8)).size() == 4, "interior degree");

        const auto serial_a = run(graph, "random", 7, false);
        const auto serial_b = run(graph, "random", 7, false);
        require(serial_a.legal, "serial result must be legal");
        require(serial_a.route_hash == serial_b.route_hash, "serial output must be deterministic");
        require(serial_a.total_wirelength == serial_b.total_wirelength,
                "serial wirelength must be deterministic");

        const auto speculative_a = run(graph, "random", 7, true);
        const auto speculative_b = run(graph, "random", 7, true);
        require(speculative_a.legal, "speculative result must be legal");
        require(speculative_a.route_hash == speculative_b.route_hash,
                "speculative output must be deterministic");
        require(speculative_a.total_wirelength == speculative_b.total_wirelength,
                "speculative wirelength must be deterministic");
        require(speculative_a.metrics.commits >= 12, "all connections must commit");
        require(speculative_a.metrics.conflicts > 0,
                "speculative batch must exercise the conflict/replay path");
        require(speculative_a.route_hash == serial_a.route_hash,
                "replayed speculative execution must match fixed serial order");

        const auto cross = run(graph, "cross", 11, true);
        require(cross.legal, "cross stress result must be legal");

        const fpga_acc::GridRoutingGraph constrained(8, 8, 1);
        auto impossible_connections = fpga_acc::make_synthetic_connections(
            constrained, 24, 3, "cross", 2);
        fpga_acc::RouterConfig impossible_config;
        impossible_config.max_iterations = 5;
        const auto impossible = fpga_acc::route_connections(
            constrained, std::move(impossible_connections), impossible_config);
        require(!impossible.legal, "overconstrained case must be preserved as a failure");
        std::cout << "router_tests: PASS\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "router_tests: FAIL: " << error.what() << '\n';
        return 1;
    }
}
