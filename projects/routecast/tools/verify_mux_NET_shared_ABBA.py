"""Audit ABBA bindings and outputs independently from timed runner."""
import json,statistics
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/mux_NET_shared_ABBA_2026-10-06'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and r['complete'] and len(r['rows'])==4
for n,h in p['sources_sha256'].items():assert sha(root/'tools'/n)==h
c=p['case'];assert sha(c['endpoint_path'])==c['endpoint_sha256'];assert sha(c['baseline'])==c['baseline_sha256']
old=json.loads(Path(c['baseline']).read_text());times={'original':[],'shared':[]}
for i,row in enumerate(r['rows']):
 name=p['order'][i];assert row['index']==i and row['implementation']==name
 file=out/f'{i}_{name}.json';assert sha(file)==row['output_sha256'];q=json.loads(file.read_text())
 assert {k:v for k,v in q.items() if k!='events'}=={k:v for k,v in old.items() if k!='events'}
 assert len(q['events'])==len(old['events'])
 for a,b in zip(q['events'],old['events']):assert {k:v for k,v in a.items() if k!='expanded'}=={k:v for k,v in b.items() if k!='expanded'}
 assert sum(e['expanded'] for e in q['events'])==row['expanded_nodes']
 if name=='original':assert q==old
 times[name].append(row['search_s'])
means={k:statistics.mean(v) for k,v in times.items()}
result={'protocol_sha256':sha(out/'protocol.json'),'receipt_sha256':sha(out/'receipt.json'),'all_four_runs_exact_policy_parity':True,'times_s':times,'means_s':means,'shared_over_original_mean_ratio':means['shared']/means['original'],'scope':'One ABBA block largest mux case, shared context excludes setup; no end-to-end, statistical confidence or general pressure accuracy claim.'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
