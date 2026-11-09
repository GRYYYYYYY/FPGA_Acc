"""Independent backward full-DAG/control audit for one immutable completed case."""
import json,sys
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];w,i=map(int,sys.argv[1:]);out=ROOT/'experiments/mux_net_slack_online_loop_2026-10-06';file=out/f'w{w}_m{i}/result.json';d=json.loads(file.read_text());a=json.loads((ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json').read_text());tgf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(tgf.read_text());mapping=json.loads(mf.read_text());incoming={int(n):[] for n in tg['nodes']}
for eid,e in tg['edges'].items():
 if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
def evaluate(b):
 @lru_cache(None)
 def arrival(n):
  return max([F(0)]+[arrival(u)+(b[str(a['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9) for u,eid in incoming[n]])
 return max(arrival(int(n)) for n,kind in tg['nodes'].items() if kind=='SINK')
seed=json.loads((ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json').read_text())
slack_file=ROOT/f'experiments/mux_net_slack_budgets_2026-10-06/w{w}_m{i}.json';assert d['initial_budget_sha256']==sha(slack_file);seed['budgets_ns']=json.loads(slack_file.read_text())['budgets_ns']
for index,spec in enumerate(d['allocations']):
 assert spec['index']==index;floor={k:F(v) for k,v in spec['floor_ns'].items()};expanded=set(map(str,spec['expanded']));value=evaluate(floor);assert value==F(spec['floor_cpd_ns']);assert len(spec['restrictions'])<=16 and sum(map(len,spec['restrictions'].values()))<=32
 if spec['valid']:
  budget={k:F(v) for k,v in spec['budgets_ns'].items()};alpha=F(spec['interpolation']);assert value<=F(a['target_cpd_ns']) and all(floor[cid]<=1 for cid in expanded);assert 0<=alpha<=1 and set(budget)==set(floor)
  preserved={cid:max(F(seed['budgets_ns'][cid]),v) for cid,v in floor.items()}
  can_preserve=bool(spec['restrictions']) and all(preserved[cid]<=1 for cid in expanded) and evaluate(preserved)<=F(a['target_cpd_ns'])
  expected_policy='INITIAL_NET_SLACK_VECTOR' if not spec['restrictions'] else ('PRESERVE_INITIAL_WITH_CONDITIONAL_FLOORS' if can_preserve else 'UNIFORM_INTERPOLATION')
  assert spec['budget_policy']==expected_policy
  if not spec['restrictions']:assert budget=={cid:F(v) for cid,v in seed['budgets_ns'].items()}
  elif can_preserve:assert budget==preserved
  else:
   for cid,b in budget.items():assert b==(floor[cid]+alpha*(1-floor[cid]) if cid in expanded else floor[cid])
  assert all(budget[cid]>=floor[cid] and budget[cid]<=1 for cid in expanded)
  assert evaluate(budget)==F(spec['budget_cpd_ns'])<=F(a['target_cpd_ns'])
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
(file.parent/'control_timing_verification.json').write_text(json.dumps(dict(result_sha256=sha(file),verifier_sha256=sha(Path(__file__)),allocations=len(d['allocations']),attempts=len(trace),scope='Independent backward recurrence/interpolation and cumulative trace provenance/release set audit. Does not independently prove newly raised shortest floors, physical paths/capacity or native STA.'),indent=2)+'\n');print(w,i,'verified timing/control',len(trace),'attempts')
