"""Retrospective cold-delay transfer and budget coverage, never predictor input."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,deque
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_bounded_branch_online_loop_2026-10-06';cold=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06';out=ROOT/'experiments/mux_branch_cold_budget_coverage_2026-10-06';out.mkdir(exist_ok=True);protocol=json.loads((base/'protocol.json').read_text());cr=json.loads((cold/'receipt.json').read_text());cv=json.loads((cold/'verification.json').read_text());assert cv['receipt_sha256']==sha(cold/'receipt.json');coldrows={(r['width'],r['index']):r for r in cr['rows']};rows=[];bindings={};last=None
for case in protocol['cases']:
 w,i=case['width'],case['index'];file=base/f'w{w}_m{i}/result.json'
 if not file.exists():continue
 af=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';a=json.loads(af.read_text());sf=cold/f'mux_w{w}_m{i}_0/accepted_state.json';s=json.loads(sf.read_text());assert sha(sf)==coldrows[w,i]['rounds'][0]['snapshot_sha256'];bindings[str(af)]=sha(af);bindings[str(Path(case['target']))]=sha(Path(case['target']));bindings[str(file)]=sha(file);bindings[str(sf)]=sha(sf)
 if w!=last:
  gf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(gf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];bindings[str(gf)]=sha(gf);bindings[str(mf)]=sha(mf);tg=json.loads(gf.read_text());mapping=json.loads(mf.read_text());adj=defaultdict(list);ind={int(n):0 for n in tg['nodes']}
  for eid,e in tg['edges'].items():
   if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
  queue=deque(n for n,v in ind.items() if not v);order=[]
  while queue:
   u=queue.popleft();order.append(u)
   for v,eid in adj[u]:
    ind[v]-=1
    if not ind[v]:queue.append(v)
  assert len(order)==len(ind);last=w
 delays={r['connection_id']:F(r['answer']['delay']*10**9,s['scale']) for r in s['records']};target=json.loads(Path(case['target']).read_text());assert {r['connection_id']:r['net_id'] for r in s['records']}=={q['connection_id']:q['net_id'] for q in target['connections']};arrival={n:F(0) for n in order}
 for u in order:
  for v,eid in adj[u]:
   delay=delays[a['edge_connection_ids'][eid]]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9;arrival[v]=max(arrival[v],arrival[u]+delay)
 cpd=max(arrival[int(n)] for n,k in tg['nodes'].items() if k=='SINK');native=F(str(coldrows[w,i]['rounds'][0]['native']['cpd_ns']));d=json.loads(file.read_text());coverage=[]
 for attempt in d['attempts']:
  spec=d['allocations'][attempt['allocation_index']];violations=[cid for cid,value in delays.items() if value>F(spec['budgets_ns'][str(cid)])];coverage.append(dict(allocation_index=spec['index'],connections_exceeding_budget=violations,expanded_exceeding=sum(cid in spec['expanded'] for cid in violations)))
 rows.append(dict(width=w,index=i,cold_model_cpd_ns=str(cpd),cold_native_printed_cpd_ns=str(native),model_transfer_difference_ns=str(cpd-native),model_target_ns=a['target_cpd_ns'],cold_model_meets_target=cpd<=F(a['target_cpd_ns']),cold_native_printed_meets_target=native<=F(a['target_cpd_ns']),allocations=coverage))
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(base/'protocol.json'),source_sha256=sha(Path(__file__)),cold_receipt_sha256=sha(cold/'receipt.json'),cold_verification_sha256=sha(cold/'verification.json'),bindings=bindings,rows=rows,scope='Available branch result snapshot. Retrospective global-cold delay transfer through old local/internal offsets hypothesis, numeric individual budget coverage only. Does not prove cold path satisfies branch exclusions/frozen retained paths/physical endpoint space, identical-space false rejection or global infeasibility. No input to live predictor.'),indent=2)+'\n');print([(r['width'],r['index'],r['cold_model_meets_target'],[len(a['connections_exceeding_budget']) for a in r['allocations']]) for r in rows])
