#pragma once
#include "persistroute.hpp"
#include "multiqueue.hpp"
#include <cstdint>
namespace persistroute {
constexpr std::uint32_t HBM_BANKS=8;
struct PEAssignment {std::uint16_t pe_id,hbm_bank;std::uint32_t task_begin;std::uint16_t task_count,reserved;};
struct SchedulerMetrics {std::uint32_t assigned,rejected;std::uint32_t pe_load[MQ_MAX_PE];std::uint32_t bank_load[HBM_BANKS];};
extern "C" void multi_pe_schedule(const Task tasks[MAX_TASKS],PEAssignment assignments[MAX_TASKS],std::uint32_t task_count,std::uint32_t pe_count,std::uint32_t bank_count,SchedulerMetrics* metrics);
}
