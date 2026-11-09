"""Original XML geometry and independent kept-union proof over the full cohort."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/zero_marginal_wire_admission_v1_2026-10-08';dp=D/'diagnosis.json';d=json.loads(dp.read_text());assert all(sha(f)==h for f,h in d['bindings'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);meta=json.loads(Path(case['target']).read_text());graph=Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256'];length={}
for node in ET.parse(graph).getroot().find('rr_nodes'):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[int(node.get('id'))]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
assert all(v>0 for v in length.values());queries={q['connection_id']:q for q in meta['connections']};groups=defaultdict(list)
for cid,q in queries.items():groups[q['net_id']].append(cid)
state={int(cid):path for cid,path in json.loads((R/'experiments/critical_owner_transaction_v1_2026-10-08/receipt.json').read_text())['rows'][0]['state'].items()};profile=json.loads((R/'experiments/complete_wire_search_cost_replay_v2_2026-10-08/receipt.json').read_text());guarded=events=0;seconds=0.;summaries=[]
for report,run in zip(d['passes'],profile['complete_passes']):
 assert report['name']==run['name'];receipt=json.loads((R/'experiments'/run['name']/'receipt.json').read_text());assert len(report['rows'])==len(receipt['events'])==len(run['rows'])==1929
 count=0;cost=0.;labels=edges=0
 for row,event,clock in zip(report['rows'],receipt['events'],run['rows']):
  cid=event['connection_id'];assert row['connection_id']==clock['connection_id']==cid
  kept={n for other in groups[queries[cid]['net_id']] if other!=cid for n,s in state[other]};moving={n for n,s in state[cid]};margin=sum(length.get(n,0) for n in moving-kept)
  assert margin==row['old_marginal_wire']>=0
  eligible=margin==0 and clock['searched'];assert eligible==row['certified_no_strict_wire_improvement']
  for key in ('search_seconds','labels_created','examined_edges'):assert row['baseline_'+key]==clock.get(key,0)
  if eligible:
   assert not any(n in length for n in moving-kept) and event['status']!='COMMIT';count+=1;cost+=clock['search_seconds'];labels+=clock['labels_created'];edges+=clock['examined_edges']
  if event['status']=='COMMIT':state[cid]=event['new_path']
  events+=1
 assert receipt['state']=={str(cid):path for cid,path in state.items()} and count==report['guarded_search_calls'] and cost==report['historical_guarded_search_seconds'] and labels==report['historical_guarded_labels'] and edges==report['historical_guarded_examined_edges']
 summaries.append(dict(name=run['name'],certified_no_strict_improvement_queries=count,historical_search_seconds=cost));guarded+=count;seconds+=cost
assert events==d['complete_events']==5787 and guarded==d['guarded_search_calls'] and seconds==d['historical_guarded_search_seconds'] and all(sha(f)==h for f,h in d['bindings'].items())
out=dict(bindings={**d['bindings'],str(dp):sha(dp),str(Path(__file__)):sha(Path(__file__))},complete_events=events,all_original_xml_marginal_and_no_improvement_certificates_pass=True,certified_guarded_calls=guarded,historical_guarded_search_seconds=seconds,passes=summaries,scope='Any candidate union includes the fixed kept nodes, and original channel geometry is nonnegative. Zero old marginal wire therefore forbids strict single-query union-wire reduction independently of RC/occupancy constraints. Existing paths retained; original budget failures not admitted. Full census only; no actual optimized timing or end-to-end speedup.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'},flush=True)
