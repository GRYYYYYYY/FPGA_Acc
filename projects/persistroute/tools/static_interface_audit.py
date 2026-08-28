#!/usr/bin/env python3
"""Fail fast when HLS, packers, XRT host and RapidWright schemas drift."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
checks={
 root/"include/persistroute.hpp":["std::uint32_t id,net_id,source,sink","MQEntry* queue_data","commit_hbm_kernel"],
 root/"include/pathfinder.hpp":["PathfinderResult route_pathfinder","NetRouteTree","PathfinderIteration","TimingAnalyzer","PathfinderTimingIteration"],
 root/"include/external_timing.hpp":["make_external_timing_analyzer"],
 root/"host/pathfinder_host.cpp":["sizeof(Task)==32",".route_trees.csv","PERSISTROUTE_PRESENT_MULTIPLIER_Q","PERSISTROUTE_MIN_TIMING_ITERATIONS","PERSISTROUTE_TIMING_COMMAND",".timing_iterations.csv"],
 root/"host/accelerated_pathfinder_host.cpp":["accelerated_iterations.csv","performance_iterations.csv","execute_hbm_cmodel_batch","PERSISTROUTE_PE_COUNT","PERSISTROUTE_MIN_TIMING_ITERATIONS","PERSISTROUTE_TIMING_UPDATE_PERIOD","PERSISTROUTE_ADAPTIVE_ISSUE_MIN","PERSISTROUTE_ADAPTIVE_ISSUE_STAGNATION","PERSISTROUTE_ADAPTIVE_ISSUE_TAIL_TASKS","PERSISTROUTE_TIMING_COMMAND"],
 root/"host/accelerated_xrt_host.cpp":["accelerated_iterations.csv","performance_iterations.csv","golden_match","commit_hbm_kernel:{commit_hbm_kernel_1}","PERSISTROUTE_TASKS_PER_CU","PERSISTROUTE_MIN_TIMING_ITERATIONS","PERSISTROUTE_TIMING_UPDATE_PERIOD","PERSISTROUTE_ADAPTIVE_ISSUE_MIN","PERSISTROUTE_ADAPTIVE_ISSUE_STAGNATION","PERSISTROUTE_ADAPTIVE_ISSUE_TAIL_TASKS","PERSISTROUTE_TIMING_COMMAND",".timing_iterations.csv","sync_resources","*pes_[3].resources"],
 root/"host/multi_pe_xrt_host.cpp":["sizeof(Task)==32","group_id(arg)","search_hbm_kernel:{search_hbm_kernel_","commit_hbm_kernel:{commit_hbm_kernel_1}"],
 root/"tools/pack_hls_inputs.py":["<IIIIHHIII","PERSISTROUTE_XRT_INPUT_V1"],
 root/"tools/rapidwright_csv_to_hls.py":["<IIIIHHIII","net_id"],
 root/"rapidwright/src/main/java/edu/fpgaacc/persistroute/RapidWrightBridge.java":["\"net_id\"","net.setPIPs","PhysNetlistWriter.writePhysNetlist"],
 root/"connectivity.cfg":["nk=search_hbm_kernel:4","nk=commit_hbm_kernel:1","search_hbm_kernel_4.queue_data:HBM[30:31]","commit_hbm_kernel_1.resources0:HBM[4:5]","commit_hbm_kernel_1.resources3:HBM[28:29]"],
}
for path,tokens in checks.items():
    text=path.read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:raise SystemExit(f"interface audit failed: {path}: {token}")
print("static_interface_audit: PASS")
