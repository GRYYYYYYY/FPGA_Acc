"""Independent backward recurrence and exact maximal-grid widening audit."""
import json,sys
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
from collections import defaultdict
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];w,i=map(int,sys.argv[1:]);out=ROOT/'experiments/mux_net_slack_budgets_2026-10-06';file=out/f'w{w}_m{i}.json';d=json.loads(file.read_text());base=ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json';seed=json.loads(base.read_text());assert d['base_sha256']==sha(base);p=json.loads((out/'protocol.json').read_text());assert p['source_sha256']==sha(ROOT/'tools/prepare_mux_net_slack_budgets.py');case=next(c for c in p['cases'] if (c['width'],c['index'])==(w,i));assert all(sha(f)==h for f,h in case['inputs'].items())
if d['status']=='PRIOR_ALLOCATION_SKIP':assert seed['status']!='CRITICAL_RELEASE_VECTOR_CONSTRUCTED'
else:
 assert seed['status']=='CRITICAL_RELEASE_VECTOR_CONSTRUCTED';old=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';assert d['old_metadata_sha256']==sha(old) and d['target_endpoint_sha256']==sha(case['target']);meta=json.loads(old.read_text());gf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(gf)==seed['graph_sha256'] and sha(mf)==seed['mapping_sha256'];tg=json.loads(gf.read_text());mapping=json.loads(mf.read_text());incoming={int(n):[] for n in tg['nodes']}
 for eid,e in tg['edges'].items():
  if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
 def evaluate(b):
  @lru_cache(None)
  def arrival(n):return max([F(0)]+[arrival(u)+(b[str(meta['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in meta['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9) for u,eid in incoming[n]])
  return max(arrival(int(n)) for n,k in tg['nodes'].items() if k=='SINK')
 ep=json.loads(Path(case['target']).read_text());expanded=set(seed['expanded_connection_ids']);assert d['expanded_connection_ids']==sorted(expanded);groups=defaultdict(list)
 for q in ep['connections']:
  if q['connection_id'] in expanded:groups[q['net_id']].append(q['connection_id'])
 assert [r['net_id'] for r in d['trace']]==sorted(groups);budget={k:F(v) for k,v in seed['budgets_ns'].items()};initial=dict(budget);assert d['initial_budgets_ns']==seed['budgets_ns'];target=F(seed['target_cpd_ns']);assert target==F(d['target_cpd_ns']);grid=F(1,2**24)
 for row in d['trace']:
  cids=sorted(groups[row['net_id']]);assert row['connection_ids']==cids;before=dict(budget);alpha=F(row['alpha']);assert 0<=alpha<=1 and (alpha/grid).denominator==1
  def vector(value):
   trial=dict(before)
   for cid in cids:trial[str(cid)]=before[str(cid)]+value*(1-before[str(cid)])
   return trial
  cap_cpd=evaluate(vector(F(1)));assert cap_cpd==F(row['cap_cpd_ns']);budget=vector(alpha);assert evaluate(budget)==F(row['budget_cpd_ns'])<=target
  if cap_cpd<=target:assert alpha==1
  else:assert alpha<1 and evaluate(vector(alpha+grid))>target
 assert budget=={k:F(v) for k,v in d['budgets_ns'].items()} and evaluate(budget)==F(d['model_budget_cpd_ns'])<=target;assert all(budget[k]>=initial[k] for k in budget);assert all(budget[str(cid)]<=1 for cid in expanded);assert all(budget[k]==initial[k] for k in budget if int(k) not in expanded)
(out/f'w{w}_m{i}_verification.json').write_text(json.dumps(dict(result_sha256=sha(file),verifier_sha256=sha(Path(__file__)),scope='Independent backward fullDAG, fixed NET order/wholeNET mask, exact perstep monotone budget raising and maximal24bit dyadic alpha, caps/retained invariance. Original floor/offset model remains hypothesis, no native routing acceptance.'),indent=2)+'\n');print(w,i,'verified NET slack budget')
