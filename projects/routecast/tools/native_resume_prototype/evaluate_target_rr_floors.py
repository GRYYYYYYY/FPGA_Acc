"""Offline compare independently produced target floors with archived working delays."""
import json,sys
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];w,i=map(int,sys.argv[1:]);out=ROOT/f'experiments/native_resume_target_rr_floors_w{w}_m{i}_2026-10-07';rp=out/'receipt.json';vp=out/'verification.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert v['receipt_sha256']==sha(rp)
ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';meta=json.loads(ep.read_text());assert sha(ep)==json.loads((out/'protocol.json').read_text())['inputs'][str(ep)]
lookup=defaultdict(list)
for row in r['rows']:
 q=row['query'];lookup[meta['net_names'][str(q['net_id'])],q['source'],q['sink']].append(row)
trace=ROOT/'experiments/native_resume_decision_audit_2026-10-07/receipt.json';tr=json.loads(trace.read_text());rows=[];bindings={str(f):sha(f) for f in (rp,vp,ep,trace)}
for mode in ('workflow','cold'):
 q=next(x for x in tr['rows'] if x['width']==w and x['mode']==mode);assert all(sha(f)==h for f,h in q['files'].items())
 last=max(int(x[1]) for x in q['events'] if x[0]=='RC_DECISION');route=ROOT/f'experiments/native_resume_decision_audit_2026-10-07/w{w}_m{i}_{mode}/output.route';bindings[str(route)]=sha(route);paths=physical_paths(route);sources={name:{p[0][0] for p in ps} for name,ps in paths.items() if ps};assert all(len(s)==1 for s in sources.values())
 records=[]
 for event in q['events']:
  if event[0]!='RC_DECISION' or int(event[1])!=last:continue
  name=event[3];sink=int(event[5]);key=name,next(iter(sources[name])),sink;options=lookup[key];assert options and len({x['minimum_integer'] for x in options})==1
  floor=F(options[0]['minimum_integer']*10**9,r['scale']);current=F(event[7])*10**9;saved=F(event[8])*10**9
  records.append(dict(net=name,native_pin=int(event[4]),rr_sink=sink,connection_ids=[x['query']['connection_id'] for x in options],reason=event[6],criticality=event[9],threshold=event[10],floor_ns=str(floor),working_delay_ns=str(current),saved_bound_ns=str(saved),working_minus_floor_ns=str(current-floor),saved_minus_floor_ns=str(saved-floor),passes_criticality=F(event[9])>=F(event[10])))
 assert len(records)==len(r['rows']);critical=[x for x in records if x['passes_criticality']];rows.append(dict(mode=mode,connections=len(records),critical_connections=len(critical),floor_exceeds_working_by_more_than_1fs=sum(F(x['floor_ns'])>F(x['working_delay_ns'])+F(1,10**6) for x in records),critical_delay_rejected_with_positive_floor_gap=sum(x['reason']=='delay' and F(x['saved_minus_floor_ns'])>0 for x in critical),mean_working_minus_floor_ns=str(sum(F(x['working_minus_floor_ns']) for x in records)/len(records)),records=records))
result=dict(bindings=bindings,producer_sha256=sha(Path(__file__)),rows=rows,scope='Estimator reads no native route/labels. Offline evaluation joins all target RR pairs to last inspected working delays, not final restored STA. Relaxed optimism and prior-bound gaps do not guarantee legal repairs or full timing improvement; no joint route or end-to-end speed claim.')
(out/'evaluation.json').write_text(json.dumps(result,indent=2)+'\n');print(w,[(x['mode'],x['critical_connections'],x['critical_delay_rejected_with_positive_floor_gap'],x['floor_exceeds_working_by_more_than_1fs']) for x in rows])
for row in rows:
 for x in row['records']:
  if w==16 and x['net']=='d6_9' and x['native_pin']==1:print(row['mode'],{k:x[k] for k in ('floor_ns','working_delay_ns','saved_bound_ns')})
