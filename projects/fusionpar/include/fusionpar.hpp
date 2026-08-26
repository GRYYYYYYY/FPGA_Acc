#pragma once
#include <cstdint>
namespace fusionpar {
constexpr std::uint32_t MAX_MOVES=1024,MAX_AFFECTED=8192,MAX_RESOURCES=8192;
struct Move {std::uint32_t instance_id;std::uint16_t old_x,old_y,new_x,new_y;std::uint32_t place_version;std::uint16_t predicted_overflow_q,flags;std::uint32_t affected_begin;std::uint16_t affected_count,repair_budget;};
struct AffectedConnection {std::uint32_t connection_id,resource_id,resource_version;std::int16_t occupancy_delta;std::uint16_t detour_q;};
struct Resource {std::uint16_t occupancy,capacity;std::uint32_t version;};
struct MoveResult {std::uint16_t status,repair_action;std::uint32_t new_place_version;std::uint32_t conflict_connection;};
struct Metrics {std::uint32_t committed,rejected,conflicts,repair_tasks;std::uint64_t reused_state_bytes;};
extern "C" void fusionpar_kernel(Move moves[MAX_MOVES],const AffectedConnection affected[MAX_AFFECTED],Resource resources[MAX_RESOURCES],MoveResult results[MAX_MOVES],std::uint32_t move_count,std::uint32_t affected_total,std::uint32_t resource_count,std::uint16_t sketch_reject_q,std::uint16_t detour_repair_q,Metrics* metrics);
}
