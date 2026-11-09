"""Independent serialized audit of all18 real-RR shared-search forecasts."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_NET_shared_parity_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and r['complete'] and len(r['rows'])==len(p['cases'])==18
for n,h in p['sources_sha256'].items():assert sha(root/'tools'/n)==h
counts={}
for c,row in zip(p['cases'],r['rows']):
 for k in ['data_width','channels','mode']:assert row[k]==c[k]
 assert sha(c['endpoint_path'])==c['endpoint_sha256'] and sha(c['baseline'])==c['baseline_sha256']
 file=out/f"gf2_d{c['data_width']}_w{c['channels']}_{c['mode']}.json";assert sha(file)==row['output_sha256'];q=json.loads(file.read_text());old=json.loads(Path(c['baseline']).read_text())
 assert {k:v for k,v in q.items() if k!='events'}=={k:v for k,v in old.items() if k!='events'}
 assert len(q['events'])==len(old['events'])
 for a,b in zip(q['events'],old['events']):assert {k:v for k,v in a.items() if k!='expanded'}=={k:v for k,v in b.items() if k!='expanded'}
 assert row['status']==q['status'] and row['completed_connections']==q['completed_connections'];key=c['mode']+':'+q['status'];counts[key]=counts.get(key,0)+1
v={'protocol_sha256':sha(out/'protocol.json'),'receipt_sha256':sha(out/'receipt.json'),'cases':18,'all_paths_costs_ledger_failure_and_commits_exact':True,'status_counts':counts,'scope':'GF2 real-RR hard and soft cohort parity; expansion events intentionally different. No improved pressure accuracy or native legal route claim.'}
(out/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v)
