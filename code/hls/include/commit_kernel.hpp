#pragma once

#include <cstdint>

namespace fpga_acc_hls {

constexpr std::uint32_t kMaxResources = 4096;
constexpr std::uint32_t kMaxEntries = 1024;

struct ResourceWord {
    std::uint16_t occupancy;
    std::uint16_t capacity;
    std::uint32_t version;
};

struct ReadEntry {
    std::uint32_t resource_id;
    std::uint32_t observed_version;
};

struct WriteEntry {
    std::uint32_t resource_id;
    std::int16_t delta_occupancy;
    std::uint16_t flags;
};

struct CommitResult {
    std::uint32_t committed;
    std::uint32_t conflict_resource;
    std::uint32_t updated_resources;
};

extern "C" void commit_kernel(
    ResourceWord resources[kMaxResources],
    const ReadEntry reads[kMaxEntries],
    const WriteEntry writes[kMaxEntries],
    std::uint32_t resource_count,
    std::uint32_t read_count,
    std::uint32_t write_count,
    CommitResult* result);

}  // namespace fpga_acc_hls
