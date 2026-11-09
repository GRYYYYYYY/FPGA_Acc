"""Authenticate fresh native metrics, placements and route identities."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha,placements
root=Path('experiments/elliptic_native_candidate_labels_2026-10-05');p=json.loads((root/'protocol.json').read_text());r=json.loads((root/'receipt.json').read_text());assert r['protocol_sha256']==sha(root/'protocol.json')
assert all(sha(f)==h for f,h in p['inputs_sha256'].items());assert all(sha(root/'source'/f)==h for f,h in p['source_sha256'].items());assert len(r['rows'])==9
base=r['rows'][0];accepted=[]
for row in r['rows']:
 cid=row['candidate_id'];native=root/f'candidate_{cid}';receipt=json.loads((native/'receipt.json').read_text());protocol=json.loads((native/'protocol.json').read_text());assert sha(native/'receipt.json')==row['native_receipt_sha256'];assert sha(native/'protocol.json')==receipt['protocol_sha256'] and receipt['exit_code']==0
 text=(native/'vpr_stdout.txt').read_text();assert sha(native/'vpr_stdout.txt')==receipt['log_sha256'];assert int(re.search(r'Total wirelength:\s*(\d+)',text)[1])==row['wirelength'];assert float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text)[1])==row['cpd_ns']
 route=Path(receipt['final_route']['path']);place=route.with_suffix('.place');assert sha(route)==receipt['final_route']['sha256'];assert placements(place,protocol['inputs']['net']['sha256'])==placements(protocol['inputs']['place']['path'],protocol['inputs']['net']['sha256'])
 header=route.read_text().splitlines()[0];assert re.search(r'Placement_ID:\s*SHA256:([0-9a-f]{64})',header)[1]==sha(place)
 if row['wirelength']<base['wirelength'] and row['cpd_ns']<=base['cpd_ns']:accepted.append(cid)
assert {x['candidate_id'] for x in r['rows']}==set(range(9))
a={'session_id':31520,'exit_code':0,'all_nine_native_runs_authenticated':True,'accepted_candidates':accepted,'baseline_wirelength':base['wirelength'],'baseline_cpd_ns':base['cpd_ns'],'candidate_wirelength_deltas':{str(x['candidate_id']):x['wirelength']-base['wirelength'] for x in r['rows'][1:]},'auditor_sha256':sha(__file__),'receipt_sha256':sha(root/'receipt.json'),'protocol_sha256':sha(root/'protocol.json'),'limitations':['single seed per case','no acceptable improving candidate in this cohort','does not establish predictor ranking quality']}
(root/'native_labels_audit.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a))
