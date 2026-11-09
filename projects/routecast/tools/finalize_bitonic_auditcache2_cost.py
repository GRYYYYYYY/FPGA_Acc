"""Bind actual same-run workflow/baseline clocks and all selected evidence."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];w=ROOT/'experiments/bitonic_auditcache2_acceptance_workflow_2026-10-07';b=ROOT/'experiments/bitonic_auditcache2_cold_cost_baseline_2026-10-07';artifacts={}
def bound(directory):
 p=json.loads((directory/'protocol.json').read_text());r=json.loads((directory/'receipt.json').read_text());assert r['complete'] and r['protocol_sha256']==sha(directory/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items());assert all(sha(directory/(x['stage']+'.log'))==x['log_sha256'] for x in r['stages'])
 for name in ['protocol.json','receipt.json']:artifacts[str(directory/name)]=sha(directory/name)
 return p,r
wp,wr=bound(w);bp,br=bound(b);selected=[]
for tag in ['bitonic_workflow_auditcache2_selected_state','bitonic_auditcache2_baseline_selected_state']:
 p=ROOT/f'experiments/{tag}_2026-10-07';r=json.loads((p/'receipt.json').read_text());v=json.loads((p/'verification.json').read_text());assert r['complete'] and v['receipt_sha256']==sha(p/'receipt.json');assert all(sha(f)==h for row in r['rows'] for f,h in row['files'].items());assert sum(row['connections'] for row in v['rows'])==6955
 for name in ['receipt.json','verification.json']:artifacts[str(p/name)]=sha(p/name)
 selected.append(v['rows'])
assert [r['selection'] for r in selected[0]]==['cold','cold','candidate'] and all(r['selection']=='cold' for r in selected[1])
for a,c in zip(selected[0],selected[1]):
 assert a['count']==c['count'] and a['zero_fixup_FULL_STA'] and c['zero_fixup_FULL_STA'];assert float(a['cpd_ns'])<=float(c['cpd_ns']) and a['wirelength']<=c['wirelength']
for n in [4,8,16]:
 a=ROOT/f'experiments/bitonic_workflow_auditcache2_swapped_cold_2026-10-07/n{n}';c=ROOT/f'experiments/bitonic_auditcache2_baseline_swapped_cold_2026-10-07/n{n}'
 assert all(sha(a/f)==sha(c/f) for f in ['design.blif','design.net','design.place','design.route'])
ws=wr['workflow_seconds'];bs=br['baseline_seconds'];assert ws>=sum(x['seconds'] for x in wr['stages']) and bs>=sum(x['seconds'] for x in br['stages'])
e=dict(artifacts_sha256=artifacts,finalizer_sha256=sha(Path(__file__)),workflow_seconds=ws,baseline_seconds=bs,workflow_over_baseline=ws/bs,net_time_gain_seconds=bs-ws,selected_workflow=selected[0],selected_baseline=selected[1],workflow_stages=wr['stages'],baseline_stages=br['stages'],scope='Serial single-run prepared input observation. Full candidate frontend/seed ledger/staging/query proof/native/canonical/cold oracle/selected state proof counted. Baseline fresh cold route/canonical/selected endpoint-ledger proof with cache clear; OS/module caches not reset. Extra finalizer outside both clocks. Original mapped netlist/initial placement/seed route/RR graph and compilation excluded. This conservative subprocess implementation is not a theoretical lower bound or strict held-out family result.')
(w/'final_evidence.json').write_text(json.dumps(e,indent=2)+'\n');print(ws,bs,ws/bs)
