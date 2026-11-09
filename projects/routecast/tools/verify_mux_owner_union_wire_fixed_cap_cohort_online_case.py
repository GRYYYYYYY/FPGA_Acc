"""Independent backward full-DAG/control audit for one immutable completed case."""
import json,sys
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];w,i=map(int,sys.argv[1:]);out=ROOT/'experiments/mux_owner_union_wire_fixed_cap_cohort_2026-10-07';file=out/f'w{w}_m{i}/result.json';d=json.loads(file.read_text());a=json.loads((ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json').read_text());tgf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(tgf.read_text());mapping=json.loads(mf.read_text());incoming={int(n):[] for n in tg['nodes']}
for eid,e in tg['edges'].items():
 if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
def evaluate(b):
 @lru_cache(None)
 def arrival(n):
  return max([F(0)]+[arrival(u)+(b[str(a['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9) for u,eid in incoming[n]])
 return max(arrival(int(n)) for n,kind in tg['nodes'].items() if kind=='SINK')
seed=json.loads((ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json').read_text())
assert d['initial_floor_seed_sha256']==sha(ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json')
assert d['fixed_cap_contract_sha256']==sha(ROOT/'experiments/fixed_connection_cap_contract_2026-10-07/verification.json')
for index,spec in enumerate(d['allocations']):
 assert spec['index']==index;floor={k:F(v) for k,v in spec['floor_ns'].items()};expanded=set(map(str,spec['expanded']));value=evaluate(floor);assert value==F(spec['floor_cpd_ns']);assert len(spec['restrictions'])<=16 and sum(map(len,spec['restrictions'].values()))<=32
 if spec['valid']:
  budget={k:F(v) for k,v in spec['budgets_ns'].items()};alpha=None if spec['interpolation'] is None else F(spec['interpolation']);assert value<=F(a['target_cpd_ns']) and all(floor[cid]<=1 for cid in expanded);assert set(budget)==set(floor)
  assert spec['budget_policy']=='FIXED_CONNECTION_CAP_ACTUAL_POSTCHECK' and alpha is None
  assert budget=={cid:F(1) if cid in expanded else max(F(1),v) for cid,v in floor.items()}
  assert all(budget[cid]>=floor[cid] and budget[cid]<=1 for cid in expanded)
  assert evaluate(budget)==F(spec['budget_cpd_ns'])
  # Fixed caps are search heuristics; actual complete-vector target check below.
result=d['result'];trace=result['trace'];assert len(trace)==len(d['attempts'])<=4
if trace:assert trace[0]['restrictions']=={}
for j,(entry,attempt) in enumerate(zip(trace,d['attempts'])):
 spec=d['allocations'][attempt['allocation_index']];assert spec['valid'] and spec['restrictions']==entry['restrictions'];candidate=attempt['update']['repair'] or attempt['update']['incremental'];assert candidate==entry['candidate'];initial=attempt['update']['incremental'];assert set(initial['affected']['affected_complete_net_connection_ids'])==set(spec['expanded'])
 if entry['parent'] is not None:
  assert entry['parent']<j and entry['depth']==trace[entry['parent']]['depth']+1
  old=trace[entry['parent']]['restrictions'];new=entry['restrictions'];assert all(k in new and set(new[k])>=set(v) for k,v in old.items()) and old!=new
  observation=trace[entry['parent']]['observation'];assert observation['query']==trace[entry['parent']]['candidate']['failure']['query'];added={(int(net),n) for net,nodes in new.items() for n in nodes if n not in old.get(net,[])};allowed={(net,b['node']) for b in observation['blockers'] for net in [observation['query']['net_id'],*b['owners']]};assert added and added<=allowed
if result['status']=='ATTEMPT_LIMIT':assert len(trace)==4 and trace[-1]['candidate']['failure'] is not None
if result['status']=='COMPLETE_CANDIDATE':assert result['candidate']['failure'] is None and result['candidate']['completed_connections']==result['candidate']['required_connections']
model=d['candidate_model_gate']
if result['status']=='COMPLETE_CANDIDATE':
 actual={str(q['connection_id']):F(q['answer']['delay']*10**9,result['candidate']['scale']) for q in result['candidate']['records']}
 assert set(actual)==set(seed['floor_ns'])
 cpd=evaluate(actual);assert cpd==F(model['actual_cpd_ns']) and F(model['target_cpd_ns'])==F(a['target_cpd_ns'])
 assert model['status']==('ACTUAL_MODEL_PASS_NATIVE_PENDING' if cpd<=F(a['target_cpd_ns']) else 'ACTUAL_MODEL_TIMING_REJECTED')
else:assert model['status']=='NOT_COMPLETE'
(file.parent/'control_timing_verification.json').write_text(json.dumps(dict(result_sha256=sha(file),verifier_sha256=sha(Path(__file__)),allocations=len(d['allocations']),attempts=len(trace),scope='Independent backward recurrence/fixed-cap budget and cumulative trace provenance/release set audit. Does not independently prove newly raised shortest floors, physical paths/capacity or native STA.'),indent=2)+'\n');print(w,i,'verified timing/control',len(trace),'attempts')
