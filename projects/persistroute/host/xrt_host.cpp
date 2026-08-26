#include "persistroute.hpp"

#include <xrt/xrt_bo.h>
#include <xrt/xrt_device.h>
#include <xrt/xrt_kernel.h>

#include <chrono>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

using namespace persistroute;

template <typename T>
void copy_to_bo(xrt::bo& buffer, const std::vector<T>& values) {
    if (values.empty()) return;
    std::memcpy(buffer.map<void*>(), values.data(), values.size() * sizeof(T));
    buffer.sync(XCL_BO_SYNC_BO_TO_DEVICE);
}

template <typename T>
void copy_from_bo(xrt::bo& buffer, std::vector<T>& values) {
    if (values.empty()) return;
    buffer.sync(XCL_BO_SYNC_BO_FROM_DEVICE);
    std::memcpy(values.data(), buffer.map<void*>(), values.size() * sizeof(T));
}

int main(int argc, char** argv) {
    try {
        if (argc != 3) {
            std::cerr << "usage: persistroute_xrt <xclbin> <input-prefix>\n";
            return 2;
        }
        const std::string xclbin = argv[1];
        const std::string prefix = argv[2];
        // Binary input generation is deliberately separate: converters preserve source hashes.
        // The .nodes/.edges/.resources/.tasks files are flat arrays of the public structs.
        auto read_array = [&](const std::string& suffix, auto* tag) {
            using T = std::remove_pointer_t<decltype(tag)>;
            std::ifstream stream(prefix + suffix, std::ios::binary | std::ios::ate);
            if (!stream) throw std::runtime_error("cannot open " + prefix + suffix);
            const auto bytes = static_cast<std::size_t>(stream.tellg());
            if (bytes % sizeof(T)) throw std::runtime_error("misaligned input " + suffix);
            std::vector<T> values(bytes / sizeof(T)); stream.seekg(0); stream.read(reinterpret_cast<char*>(values.data()), bytes); return values;
        };
        auto nodes = read_array(".nodes", static_cast<Node*>(nullptr));
        auto edges = read_array(".edges", static_cast<Edge*>(nullptr));
        auto resources = read_array(".resources", static_cast<Resource*>(nullptr));
        auto tasks = read_array(".tasks", static_cast<Task*>(nullptr));
        std::vector<std::uint32_t> paths(MAX_TX_ENTRIES);
        std::vector<ReadEntry> reads(MAX_TX_ENTRIES);
        std::vector<PathResult> results(tasks.size());
        std::vector<Metrics> metrics(1);

        xrt::device device(0);
        const auto uuid = device.load_xclbin(xclbin);
        xrt::kernel search(device, uuid, "search_kernel");
        xrt::kernel commit(device, uuid, "commit_kernel");
        auto make_bo = [&](std::size_t bytes, xrt::kernel& kernel, int arg) { return xrt::bo(device, bytes, kernel.group_id(arg)); };
        auto bo_nodes=make_bo(nodes.size()*sizeof(Node),search,0), bo_edges=make_bo(edges.size()*sizeof(Edge),search,1);
        auto bo_resources=make_bo(resources.size()*sizeof(Resource),search,2), bo_tasks=make_bo(tasks.size()*sizeof(Task),search,3);
        auto bo_paths=make_bo(paths.size()*sizeof(std::uint32_t),search,4), bo_reads=make_bo(reads.size()*sizeof(ReadEntry),search,5);
        auto bo_results=make_bo(results.size()*sizeof(PathResult),search,6), bo_metrics=make_bo(sizeof(Metrics),search,10);
        copy_to_bo(bo_nodes,nodes);copy_to_bo(bo_edges,edges);copy_to_bo(bo_resources,resources);copy_to_bo(bo_tasks,tasks);
        const auto begin=std::chrono::steady_clock::now();
        auto search_run=search(bo_nodes,bo_edges,bo_resources,bo_tasks,bo_paths,bo_reads,bo_results,
                               static_cast<std::uint32_t>(nodes.size()),static_cast<std::uint32_t>(edges.size()),static_cast<std::uint32_t>(tasks.size()),bo_metrics);
        search_run.wait();
        // BOs are shared/importable across kernels when connectivity permits; v++ link config must map both CUs to the same HBM banks.
        auto commit_run=commit(bo_resources,bo_tasks,bo_paths,bo_reads,bo_results,
                               static_cast<std::uint32_t>(resources.size()),static_cast<std::uint32_t>(tasks.size()),bo_metrics);
        commit_run.wait();
        const auto end=std::chrono::steady_clock::now();
        copy_from_bo(bo_results,results);copy_from_bo(bo_resources,resources);copy_from_bo(bo_metrics,metrics);
        const double wall_ms=std::chrono::duration<double,std::milli>(end-begin).count();
        std::uint32_t committed=0,conflicts=0,failed=0;for(const auto&r:results){committed+=r.status==4;conflicts+=r.status==2;failed+=r.status==3;}
        std::cout << "{\"wall_ms\":"<<wall_ms<<",\"tasks\":"<<tasks.size()<<",\"committed\":"<<committed<<",\"conflicts\":"<<conflicts<<",\"failed\":"<<failed<<"}\n";
        return failed?2:0;
    } catch(const std::exception& e) { std::cerr<<"error: "<<e.what()<<"\n"; return 1; }
}
