"""Full development sequence from empty state, graph/floors construction paid."""
import json,sys,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from tree_floor_pareto_predictor_v4 import grouped_floor
from mcnc_pending_swap_observer_sequence_v14 import sequence
from remaining_delay_worker_cache_v7 import RemainingDelayCache
from source_binding_v2 import closure
base=R/'experiments/mcnc_prospective_v1_2026-10-07';out=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07';out.mkdir();inputs={};sources=closure([Path(__file__)])
for artifact in (R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute',R/'tools/capped_bound_worker_cpp_v2/main.cpp',R/'experiments/worker_cache_cost_v7_2026-10-07/verification.json',R/'experiments/dsip_observer_joint_pair_v2_2026-10-07/receipt.json'):
 inputs[str(artifact)]=sha(artifact)
proof=json.loads((R/'experiments/worker_cache_cost_v7_2026-10-07/verification.json').read_text());assert all(sha(k)==h for k,h in proof['bindings'].items())
paired=json.loads((R/'experiments/dsip_observer_joint_pair_v2_2026-10-07/receipt.json').read_text());assert all(sha(k)==h for k,h in {**paired['bindings'],**paired['files']}.items())
for name in ('bigkey','dsip','misex3'):
 ep=base/name/'endpoints.json';inputs[str(ep)]=sha(ep);inputs.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
protocol=dict(inputs=inputs,sources=sources,cases=['bigkey','dsip','misex3'],policy=dict(start='empty',order='NET/CID',max_batches=16,max_owner_nets_per_batch=4,max_pending_window=16,max_joint_nodes=64,frontier='dfs',memo='call-local NET/forbidden',cache='FIFO256, capped0.5ns, immutable snapshots and mandatory finalize',search_deadline_seconds_per_design=120,budget='max1ns,ceil1.5*inputfloor',objective='delay +0.04ns new CHAN span, Pareto10000labels',transaction='At capacity failure select ordered minimum-witness prefix, remove complete released NETs, joint-route all selected and removed; commit exact before union selected; failure retains exact before and stops. On failed non-deadline primary joint, preserve ALL selected requests, max4 release sets, each DFS64, owner4, baseline-certified domains max4/ownerchecks32. After expansion failure, up to4 fixed-forbidden domains/32 swap checks/4 release candidates, each DFS64, all selected requests retained and owner4; proposal filter heuristic for fresh joint. Exact rollback if no repair/swap solution; all new work inside global120s/16transactions.'),scope='Post-outcome development full-cohort from empty. Single-variable implementation ablation relative to v20: observer JSON-valued state copying preserves all values, insertion order and mutable isolation; primary/expansion/swap all use this clone. Same on-demand C++ worker cache backend; exact bounds/FIFO/identity/mandatory closing retained; constructor model conversion/worker init and request IPC/archive/worker closing paid. max_batches16/global120 unchanged; objective0.04ns/new CHANspan and all algorithm parameters unchanged. Same edge/occupancy memo; seed fully validated once per joint call, paid; fork copies queried NET trees, full ledger and isolated records. No occupancy-dependent solution reuse across transactions. Graph-array identity binding strengthened. New fallback is extra paid work, not an equal-work ablation. Fresh single runs, elapsed-time deadline can change explored work; no statistical/heldout or pre-selection claim. No prepared candidate/native labels, native/heldout/hardware claim. Construction/floors/search/cache/logging paid; provenance hashing and retrospective audits excluded from existing case timer.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for name in protocol['cases']:
 begin=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(base/name/'endpoints.json');construction=time.perf_counter()-begin;groups=defaultdict(set)
 for q in queries:groups[q['source']].add(q['sink'])
 start=time.perf_counter();floors={}
 for source,sinks in groups.items():floors.update({(source,sink):value for sink,value in grouped_floor(f,rc,source,sinks).items()})
 floor_seconds=time.perf_counter()-start;spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];assert rc.scale%10**11==0;penalty=4*(rc.scale//10**11);work=out/name;work.mkdir();(work/'floors.json').write_text(json.dumps([dict(source=u,sink=v,minimum_integer=d) for (u,v),d in sorted(floors.items())])+'\n');cache=RemainingDelayCache(graph,digest,f,rc,work/'bounds',max_entries=256);f=cache.fields;rc=cache.rc;start=time.perf_counter()
 def observe(event):
  (work/f'batch{event["index"]}.json').write_text(json.dumps(event)+'\n');print(name,'batch',event['index'],event['committed'],event['batch_failure'],flush=True)
 def trace(batch_index,attempt_index,release_nets,branch,states,solution):
  directory=work/f"repair_batch{batch_index}_attempt{attempt_index}_branch{branch['index']}";directory.mkdir();(directory/'branch.json').write_text(json.dumps(dict(released_net_ids=release_nets,branch=branch))+'\n')
  for net,state in states.items():(directory/f'net{net}.json').write_text(json.dumps(state)+'\n')
  if solution is not None:(directory/'joint_candidate.json').write_text(json.dumps(solution)+'\n')
 state,events,stop=sequence(f,rc,queries,floors,max_batches=16,deadline=start+120,observer=observe,spans=spans,penalty=penalty,remaining_cache=cache,repair_observer=trace);cache.finalize();state.update(graph_sha256=digest,scale=rc.scale);(work/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n');(work/'candidate.json').write_text(json.dumps(state)+'\n');rows.append(dict(name=name,construction_seconds=construction,floor_seconds=floor_seconds,sequence_seconds=time.perf_counter()-start,total_seconds=time.perf_counter()-begin,stop=stop,completed=state['completed_connections'],required=state['required_connections'],batches=len(events),commits=sum(e['committed'] for e in events),cache_summary=cache.summary(),files={str(p):sha(p) for p in work.rglob("*") if p.is_file()}));(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,stop,state['completed_connections'],len(queries),flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
