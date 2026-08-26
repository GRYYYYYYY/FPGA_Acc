#pragma once
#include <cstdint>
namespace dieroute {
constexpr std::uint32_t MAX_DIES=8,MAX_BOUNDARIES=64,MAX_TASKS=2048;
struct Boundary {std::uint16_t src_die,dst_die,capacity,reserved;std::uint16_t delay_q,history_q;std::uint32_t version;};
struct CrossDieTask {std::uint32_t id;std::uint16_t src_die,dst_die,criticality_q,demand;std::uint32_t priority;};
struct Allocation {std::uint16_t boundary_id,status;std::uint32_t observed_version;std::uint32_t score_q;};
struct DieQueue {std::uint32_t count,critical_count,total_demand,migrations;};
struct Metrics {std::uint32_t allocated,rejected,shadow_updates,migrations;std::uint64_t total_score_q;};
extern "C" void dieroute_kernel(Boundary boundaries[MAX_BOUNDARIES],const CrossDieTask tasks[MAX_TASKS],Allocation allocations[MAX_TASKS],DieQueue queues[MAX_DIES],std::uint32_t boundary_count,std::uint32_t task_count,std::uint32_t die_count,Metrics* metrics);
}
