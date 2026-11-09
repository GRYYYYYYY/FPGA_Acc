"""Archive exact native source evidence for seed insertion and preservation barriers."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
vtr=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
out=root/'experiments/native_seed_entry_audit_2026-10-06';out.mkdir(exist_ok=True)
checks=[('vpr/src/route/route.cpp','init_route_structs(net_list,','Seed insertion must follow initialization, before routing iterations.'),('vpr/src/route/route_common.cpp','std::fill(route_ctx.route_trees.begin(), route_ctx.route_trees.end(), vtr::nullopt);','Initialization clears every tree.'),('vpr/src/route/route_net.cpp','num_sinks < router_opts.min_incremental_reroute_fanout || itry == 1 || ripup_high_fanout_nets','Selected NET first iteration unconditionally tears down its seed; small fanout also forces whole-net reroute.'),('vpr/src/route/route_net.cpp','if (tree.get_remaining_isinks().empty())','Uncongested complete tree can skip routing through should_route_net; fixed NET flags must not be used to mask congestion.'),('vpr/src/route/route_net.cpp','tree2.prune(connections_inf)','Partial preservation requires initialized congestion and connection reroute metadata; pruning occurs before old occupancy subtraction.')]
records=[]
for relative,needle,conclusion in checks:
 p=vtr/relative;data=p.read_bytes();lines=data.decode().splitlines();hits=[i for i,line in enumerate(lines) if needle in line];assert len(hits)==1,(relative,needle,hits);i=hits[0]
 records.append({'source':str(p),'sha256':hashlib.sha256(data).hexdigest(),'line':i+1,'excerpt':'\n'.join(lines[max(0,i-5):i+8]),'conclusion':conclusion})
(out/'source_evidence.json').write_text(json.dumps({'records':records,'scope':'Read-only source audit, not runtime seed retention evidence.','next_runtime_gates':['Insert seed after init_route_structs with normal routing selected.','Recompute tree timing and unique-NET occupancy before any should_route_net call.','Capture before/after first real routing iteration and counters for skipped/rerouted NETs.','Test congested seed without fixed flags; separately evaluate whole-net versus partial repair.','Independent original XML audit and native pin/nonconfig legality on published output.','Charge import, synchronization and search in matched cold-control timing.']},indent=2)+'\n')
print('Archived five native seed-entry checks')
