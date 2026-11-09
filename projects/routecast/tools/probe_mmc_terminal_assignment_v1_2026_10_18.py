"""All-three pre-route frames: source-only terminal assignment feasibility."""
import json,sys,time
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from terminal_assignment_feasibility_v1 import terminal_index,probe
D=R/'experiments/mmc_terminal_assignment_probe_v1_2026-10-18';D.mkdir()
core=R/'experiments/terminal_assignment_feasibility_core_v1_2026-10-18/verification.json';V=json.loads(core.read_text());assert V['status']=='pass' and V['random_graphs']==500
bindings={**V['bindings'],str(core):sha(core),**closure([Path(__file__)])};cases=['case_01','case_02','case_03'];inputs={}
for case in cases:
 M=R/'experiments/mmc_multiplacement_models_v1_2026-10-18'/case
 inputs[case]=dict(frame=str(M/'native_retained/initial.json'),proof=str(M/'initial_independent_verification_v1.json'),
                   endpoint=str(R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json'))
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,inputs=inputs,cases=cases,
 selection='Every initially overused IPIN class in each audited retained_off pre-route frame, using graph/initial ledger only. No target-native output, tail class or quality values read.',
 candidates='Same actual pre-IPIN upstream RR and unchanged prefix, substitute only actual upstream-to-IPIN and IPIN-to-same-SINK edges. Exact original RC budget unchanged. Unit IPIN capacities and one query per NET/class required; unsupported full classes reported, original all115572queries remain unchanged.',
 matching='Deterministic maximum capacitated matching, independently tested against exhaustive Hall deficiency; failed restricted graphs report Hall witness, not global unroutability.',
 scope='Feasibility proposals only; no objective-approved or atomic model updates, native runs, channel-rank gain, routing-policy change or full-flow timing gain.'),f,indent=2)
cache=Cache();frames={};summaries=[]
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items())
 for case,data in inputs.items():
  p=Path(data['proof']);v=json.loads(p.read_text());assert v['status']=='pass' and v['all115572V2budgets_matched'] and all(sha(x)==h for x,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
  frame=Path(data['frame']);endpoint=Path(data['endpoint']);frames[case]=json.loads(frame.read_text());assert frames[case]['required_connections']==frames[case]['completed_connections']==115572
  bindings[str(frame)]=sha(frame);bindings[str(endpoint)]=sha(endpoint)
 print('TERMINAL PROBE LOAD SHARED GRAPH',flush=True)
 tick=time.perf_counter();graph,digest,nodes,fields,rc,_=load_endpoints(inputs[cases[0]]['endpoint']);setup=time.perf_counter()-tick
 kinds=[n.get('type') for n in nodes];info,pools=terminal_index(fields,kinds)
 needed={eid for frame in frames.values() for r in frame['records'] for eid in r['answer']['physical_edge_ids'][-2:]}
 slots={eid:s for s,eid in enumerate(fields['edge_ids']) if eid in needed};assert slots.keys()==needed
 for case,frame in frames.items():
  ep=json.loads(Path(inputs[case]['endpoint']).read_text());assert ep['graph_sha256']==digest==frame['graph_sha256'] and frame['scale']==rc.scale
  ledger={int(n):v for n,v in frame['ledger'].items()};pressure={n for n,v in ledger.items() if v>fields['capacities'][n]}
  assert sum(ledger[n]-fields['capacities'][n] for n in pressure)==frame['overflow_units']
  requested={info[n][0] for n in pressure if kinds[n]=='IPIN' and n in info}
  unsupported_pins=sorted(n for n in pressure if kinds[n]=='IPIN' and n not in info)
  groups=defaultdict(list)
  for r in frame['records']:
   if r['sink'] in requested:groups[r['sink']].append(r)
  assert groups.keys()==requested
  rows=[probe(sink,groups[sink],ledger,fields,kinds,rc,slots,info,pools) for sink in sorted(requested)]
  status=Counter(r['status'] for r in rows);summary=dict(case=case,initial_overflow_units=frame['overflow_units'],pressure_nodes_by_type=dict(Counter(kinds[n] for n in pressure)),
   pressure_units_by_type={kind:sum(ledger[n]-fields['capacities'][n] for n in pressure if kinds[n]==kind) for kind in sorted({kinds[n] for n in pressure})},
   selected_SINK_classes=len(requested),unsupported_pressure_IPINs=unsupported_pins,class_statuses=dict(status),
   feasible_proposal_queries=sum(len(r.get('assignments',[])) for r in rows),input_queries_retained_unchanged=115572,input_state_mutated=False)
  with (D/(case+'.json')).open('x') as f:json.dump(dict(bindings={str(Path(inputs[case]['frame'])):sha(inputs[case]['frame']),str(Path(inputs[case]['proof'])):sha(inputs[case]['proof']),str(graph):digest},summary=summary,classes=rows),f,indent=2)
  summaries.append(summary);print('TERMINAL ASSIGNMENT PROBE',summary,flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 for case in cases:
  p=D/(case+'.json');bindings[str(p)]=sha(p)
 with (D/'receipt.json').open('x') as f:json.dump(dict(status='all3_feasibility_proposals_generated',bindings={**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},summaries=summaries,shared_graph_setup_seconds=setup,digest=cache.snapshot(),independent_candidate_and_Hall_verification_pending=True,
  scope='Restricted same-upstream terminal-edge feasibility only. No model commits, objective/atomic admission, budget relaxation or target-label selection; all input queries unchanged. Channel paths retained, so no claim of improved channel-density metrics.'),f,indent=2)
print('ALL3TERMINAL ASSIGNMENT PROBES GENERATED',flush=True)
