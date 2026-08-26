#pragma once

#include <array>
#include <cstdint>
#include <limits>
#include <vector>

namespace fpga_acc {

constexpr std::uint64_t kSchemaMagic = 0x5043434141475046ULL;  // "FPGAACCP"
constexpr std::uint32_t kInvalidId = std::numeric_limits<std::uint32_t>::max();

enum class ObjectType : std::uint32_t {
    Architecture = 1,
    Placement = 2,
    ConnectionTask = 3,
    ResourceState = 4,
    TimingSnapshot = 5,
    Metrics = 6,
};

#pragma pack(push, 1)
struct FileHeader {
    std::uint64_t magic = kSchemaMagic;
    std::uint16_t schema_major = 0;
    std::uint16_t schema_minor = 1;
    std::uint32_t object_type = 0;
    std::uint64_t element_count = 0;
    std::uint64_t payload_bytes = 0;
    std::array<std::uint8_t, 16> architecture_hash{};
    std::uint64_t crc64 = 0;
    std::uint32_t flags = 0;
    std::uint32_t reserved = 0;
};

struct ConnectionTask {
    std::uint32_t connection_id = 0;
    std::uint32_t net_id = 0;
    std::uint32_t source_node = 0;
    std::uint32_t sink_node = 0;
    std::uint16_t bbox_xmin = 0;
    std::uint16_t bbox_ymin = 0;
    std::uint16_t bbox_xmax = 0;
    std::uint16_t bbox_ymax = 0;
    std::uint16_t criticality_q = 0;
    std::uint16_t delay_budget_q = 0;
    std::uint32_t old_tree_offset = 0;
    std::uint32_t old_tree_length = 0;
    std::uint32_t epoch = 0;
    std::uint32_t priority = 0;
    std::uint32_t footprint_id = 0;
    std::uint32_t flags = 0;
    std::uint32_t seed_or_tie = 0;
    std::uint64_t reserved = 0;
};

struct ResourceState {
    std::uint32_t owner_or_list = kInvalidId;
    std::uint16_t occupancy = 0;
    std::uint16_t capacity = 1;
    std::uint16_t present_cost_q = 256;
    std::uint16_t history_cost_q = 0;
    std::uint32_t version = 0;
};

struct TimingSnapshot {
    std::uint16_t criticality_q = 0;
    std::uint16_t flags = 0;
    std::int32_t arrival_q = 0;
    std::int32_t required_q = 0;
    std::uint32_t delay_budget_q = 0;
};
#pragma pack(pop)

static_assert(sizeof(FileHeader) == 64, "FileHeader must be one 64-byte cache line");
static_assert(sizeof(ConnectionTask) == 64, "ConnectionTask must be 64 bytes");
static_assert(sizeof(ResourceState) == 16, "ResourceState must be 16 bytes");
static_assert(sizeof(TimingSnapshot) == 16, "TimingSnapshot must be 16 bytes");

struct ReadSetEntry {
    std::uint32_t resource_id = 0;
    std::uint32_t observed_version = 0;
};

struct WriteSetEntry {
    std::uint32_t resource_id = 0;
    std::int16_t delta_occupancy = 0;
    std::uint16_t flags = 0;
};

enum class TransactionStatus : std::uint32_t {
    Candidate = 0,
    Committed = 1,
    Conflict = 2,
    Failed = 3,
};

struct RouteTransaction {
    std::uint32_t connection_id = 0;
    std::uint32_t epoch = 0;
    std::uint32_t priority = 0;
    TransactionStatus status = TransactionStatus::Candidate;
    std::vector<ReadSetEntry> read_set;
    std::vector<WriteSetEntry> write_set;
    std::vector<std::uint32_t> candidate_path;
};

}  // namespace fpga_acc
