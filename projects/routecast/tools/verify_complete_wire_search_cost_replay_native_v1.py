"""Check full cohort/result fidelity and arithmetic of component cost observations."""
import json,math
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/complete_wire_search_cost_replay_native_v1_2026-10-08';rp=D/'receipt.json';r=json.loads(rp.read_text());p=json.loads((D/'protocol.json').read_text())
assert all(sha(f)==h for f,h in r['bindings'].items()) and all(r['bindings'][f]==h for f,h in p['bindings'].items()) and r['protocol_sha256']==sha(D/'protocol.json')
assert r['all5787_events_and_search_answers_reproduced'] and len(r['complete_passes'])==len(p['passes'])==3
bindings={**r['bindings'],str(rp):sha(rp),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(Path(__file__))};summaries=[]
for name,run in zip(p['passes'],r['complete_passes']):
 assert name==run['name'];path=D/(name+'.json');assert json.loads(path.read_text())==run;bindings[str(path)]=sha(path)
 original=json.loads((R/'experiments'/name/'receipt.json').read_text());assert len(run['rows'])==run['complete_queries']==len(original['events'])==1929 and run['search_calls']==1927
 assert [x['connection_id'] for x in run['rows']]==[x['connection_id'] for x in original['events']]==list(range(1929))
 counts=Counter();labels=expanded=examined=0
 for row,event in zip(run['rows'],original['events']):
  assert row['status']==event['status'];counts[row['status']]+=1
  if not row['searched']:assert row['connection_id'] in (785,1637) and row['status']=='RETAIN_ORIGINAL_CERTIFIED_BUDGET_INFEASIBLE';continue
  for key in ('search_seconds','maintenance_seconds'):assert math.isfinite(row[key]) and row[key]>=0
  for key in ('labels_created','labels_expanded','examined_edges'):assert row[key]==event['search'][key] and type(row[key]) is int and row[key]>=0
  labels+=row['labels_created'];expanded+=row['labels_expanded'];examined+=row['examined_edges']
 search=sum(x.get('search_seconds',0) for x in run['rows']);maintenance=sum(x.get('maintenance_seconds',0) for x in run['rows'])
 assert search==run['search_seconds'] and math.isclose(maintenance,run['maintenance_seconds'],rel_tol=1e-12,abs_tol=1e-9) and search+maintenance<=run['pass_seconds'] and dict(counts)==run['status_counts']
 assert run['initial_wire']==original['initial_wire'] and run['final_wire']==original['final_wire']
 summaries.append(dict(name=name,search_calls=1927,search_seconds=search,maintenance_seconds=maintenance,pass_seconds=run['pass_seconds'],labels_created=labels,labels_expanded=expanded,examined_edges=examined,status_counts=dict(counts)))
assert r['total_search_seconds']==sum(x['search_seconds'] for x in summaries) and r['elapsed_seconds']>=r['authentication_seconds']+r['context_seconds']+sum(x['pass_seconds'] for x in summaries)
assert all(sha(f)==h for f,h in bindings.items())
out=dict(bindings=bindings,complete_events=5787,search_calls=5781,all_complete_cohort_fidelity_and_cost_arithmetic_checks_pass=True,passes=summaries,native_calls=r['native_calls'],python_fallback_calls=r['python_fallback_calls'],native_input_preparation_seconds=r['native_input_preparation_seconds'],objective_cap=r['objective_cap'],total_search_seconds=r['total_search_seconds'],total_maintenance_seconds=sum(x['maintenance_seconds'] for x in summaries),context_seconds=r['context_seconds'],authentication_seconds=r['authentication_seconds'],elapsed_seconds=r['elapsed_seconds'],scope='Single observation of instrumented native-CPU incremental-ledger fresh searches reproducing every frozen answer and complete state; runtime observations are not a universal bound or paired speedup. Reuses certified query ceilings and one shared graph context; excludes upstream synthesis/budget/owner repair, dynamic global timing recalculation, native/canonical and full audits. Complete workflow gain remains unproved.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2),flush=True)
