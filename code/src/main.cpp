#include "fpga_acc/router.hpp"

#include <cstdlib>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

struct Options {
    std::uint32_t width = 24;
    std::uint32_t height = 24;
    std::uint32_t connections = 32;
    std::uint32_t seed = 1;
    std::uint32_t capacity = 2;
    std::uint32_t iterations = 30;
    std::uint32_t batch = 1;
    std::uint32_t threads = 1;
    std::uint32_t bbox_margin = 4;
    std::string pattern = "random";
    std::string mode = "serial";
    std::string output;
};

std::uint32_t as_u32(const char* text, const std::string& option) {
    const unsigned long value = std::stoul(text);
    if (value > 0xffffffffUL) throw std::invalid_argument(option + " exceeds uint32");
    return static_cast<std::uint32_t>(value);
}

Options parse_options(int argc, char** argv) {
    Options options;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto value = [&]() -> const char* {
            if (i + 1 >= argc) throw std::invalid_argument("missing value for " + arg);
            return argv[++i];
        };
        if (arg == "--width") options.width = as_u32(value(), arg);
        else if (arg == "--height") options.height = as_u32(value(), arg);
        else if (arg == "--connections") options.connections = as_u32(value(), arg);
        else if (arg == "--seed") options.seed = as_u32(value(), arg);
        else if (arg == "--capacity") options.capacity = as_u32(value(), arg);
        else if (arg == "--iterations") options.iterations = as_u32(value(), arg);
        else if (arg == "--batch") options.batch = as_u32(value(), arg);
        else if (arg == "--threads") options.threads = as_u32(value(), arg);
        else if (arg == "--bbox-margin") options.bbox_margin = as_u32(value(), arg);
        else if (arg == "--pattern") options.pattern = value();
        else if (arg == "--mode") options.mode = value();
        else if (arg == "--output") options.output = value();
        else if (arg == "--help") {
            std::cout << "persist_route_sw [--width N --height N --connections N --seed N]\n"
                         "  [--capacity N --iterations N --bbox-margin N]\n"
                         "  [--pattern random|cross|hotspot]\n"
                         "  [--mode serial|speculative --batch N --threads N] [--output file]\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown option: " + arg);
        }
    }
    if (options.mode != "serial" && options.mode != "speculative") {
        throw std::invalid_argument("mode must be serial or speculative");
    }
    if (options.width > 65535 || options.height > 65535 || options.capacity > 65535) {
        throw std::invalid_argument("width, height, and capacity must fit in 16 bits");
    }
    if (options.connections == 0 || options.capacity == 0 || options.batch == 0 ||
        options.threads == 0 || options.iterations == 0) {
        throw std::invalid_argument("connections, capacity, batch, threads, and iterations must be positive");
    }
    if (options.mode == "serial") {
        options.batch = 1;
        options.threads = 1;
    }
    return options;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const auto options = parse_options(argc, argv);
        fpga_acc::GridRoutingGraph graph(
            options.width, options.height, static_cast<std::uint16_t>(options.capacity));
        auto connections = fpga_acc::make_synthetic_connections(
            graph, options.connections, options.seed, options.pattern, options.bbox_margin);
        fpga_acc::RouterConfig config;
        config.max_iterations = options.iterations;
        config.batch_size = options.batch;
        config.worker_threads = options.threads;
        config.bbox_margin = options.bbox_margin;
        config.speculative = options.mode == "speculative";
        const auto result = fpga_acc::route_connections(graph, std::move(connections), config);
        const auto json = fpga_acc::result_to_json(
            result, graph, config, options.pattern, options.seed);
        if (!options.output.empty()) {
            std::ofstream output(options.output, std::ios::binary);
            if (!output) throw std::runtime_error("cannot open output file");
            output << json;
        }
        std::cout << json;
        return result.legal ? 0 : 2;
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
}
