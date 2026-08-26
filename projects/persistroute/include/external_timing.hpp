#pragma once

#include "pathfinder.hpp"

#include <string>

namespace persistroute {

// The command is invoked as:
//   <command> <iteration> <input.csv> <output.csv>
// It must return one numeric output row per task with columns
// task_id,criticality_q,delay_ps,slack_ps,critical_path_delay_ps.
TimingAnalyzer make_external_timing_analyzer(
 const std::string& command,
 const std::string& audit_prefix);

} // namespace persistroute
