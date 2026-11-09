"""Whole-cohort independent exactRC/history/cut/ownership/queue event audit."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_pressure_frontier_repair_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==r['protocol_sha256'] and r['all_cases_retained'];assert all(sha(root/'tools'/n)==h for n,h in p['sources_sha256'].items());rows=[]
for c,row in zip(p['cases'],r['rows']):
 w=c['data_width'];ch=c['channels'];prior=Path(c['directory']);d=out/f'gf2_d{w}_w{ch}';assert all(sha(f)==h for f,h in c['bindings'].items());assert sha(d/'receipt.json')==row['candidate_sha256'];a=d/'audit';a.mkdir();s=(root/'tools/verify_ex5p_bounded_history_repair.py').read_text();start=s.index('root=Path(__file__)');end=s.index('audit=ImmutableXMLAudit',start);s=s[:start]+f"root=Path({str(root)!r});out=Path({str(a)!r});r=json.loads(Path({str(d/'receipt.json')!r}).read_text());prior=json.loads(Path({str(prior/'receipt.json')!r}).read_text());ep=json.loads(Path({str(prior/'endpoints.json')!r}).read_text());"+s[end:];end=s.index('assert repairs==r[\'repairs\']==2');s=s[:end]+'''assert repairs==r['repairs'] and [records[k] for k in sorted(records)]==r['records'] and dict(ledger)=={int(n):c for n,c in r['ledger'].items()} and dict(history)=={int(n):c for n,c in r['history'].items()}
assert len(records)==r['completed_connections'] and len(queries)==r['required_connections'] and all(c<=audit.caps[n] for n,c in ledger.items())
q,other,answer=last
assert r['failure']['query']==q and not r['events'][-1]['committed']
reachable=reach(q,other)
if r['failure']['status']=='CONNECTED_BUDGET_OR_SEARCH_FAILURE':assert q['sink'] in reachable
if r['failure']['status']=='NO_RELEASABLE_OWNER':
 assert q['sink'] not in reachable
 frontier={n for u in reachable for n in adj[u] if n not in reachable} if reachable else {q['source']}
 assert not any(k!=q['net_id'] and any(n in ns for n in frontier) for k,ns in unions.items())
(out/'verification.json').write_text(json.dumps({'retained_connections':len(records),'successful_witnesses_checked':witnesses,'releases':releases,'repairs':repairs,'overflow_units':0,'multi_parent_nodes':0,'failed_query_not_committed':True,'receipt_sha256':sha(Path(RECEIPT))})+'\\n')
'''.replace('RECEIPT',repr(str(d/'receipt.json')));tool=a/'audit.py';tool.write_text('import sys\nsys.path.insert(0,'+repr(str(root/'tools'))+')\n'+s)
 with (a/'audit.log').open('w') as log:code=subprocess.run(['python3',str(tool)],stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 assert code==0;proof=json.loads((a/'verification.json').read_text());assert proof['receipt_sha256']==sha(d/'receipt.json');rows.append({'data_width':w,'channels':ch,**proof,'event_audit_sha256':sha(a/'verification.json')});print(w,ch,'repair events verified',proof['repairs'],flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'All9 retained prefixes and everyquery/release/history/residualcapacitycut/NETownership/pendingqueue independently originalXML audited. No completecandidate/nativequality/forecastbenefit established.'},indent=2)+'\n')
