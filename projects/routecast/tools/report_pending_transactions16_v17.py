"""Authenticated development ablation summary, not native QoR or a speedup proof."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
old=R/'experiments/mcnc_pending_swap_v16_2026-10-07';new=R/'experiments/mcnc_pending_swap_transactions16_v17_2026-10-07'
a=json.loads((old/'protocol.json').read_text());b=json.loads((new/'protocol.json').read_text())
assert a['inputs']==b['inputs'] and a['cases']==b['cases']
x=dict(a['policy']);y=dict(b['policy']);assert x.pop('max_batches')==8 and y.pop('max_batches')==16
assert x.pop('transaction').replace('global120s/8transactions','global120s/16transactions')==y.pop('transaction');assert x==y
bindings=closure([Path(__file__)]);receipts=[]
for directory,protocol in [(old,a),(new,b)]:
 rp=directory/'receipt.json';receipt=json.loads(rp.read_text());assert receipt['protocol_sha256']==sha(directory/'protocol.json')
 bindings[str(rp)]=sha(rp);bindings[str(directory/'protocol.json')]=sha(directory/'protocol.json');bindings.update(protocol['inputs']);bindings.update(protocol['sources'])
 for row in receipt['rows']:bindings.update(row['files'])
 receipts.append({r['name']:r for r in receipt['rows']})
assert all(sha(p)==h for p,h in bindings.items());rows=[]
for name in b['cases']:
 before=receipts[0][name];after=receipts[1][name];events=[json.loads(p.read_text()) for p in sorted((new/name).glob('batch*.json'),key=lambda p:int(p.stem[5:]))]
 assert len(events)==after['batches']<=16 and sum(e['committed'] for e in events)==after['commits']
 rows.append(dict(name=name,before_completed=before['completed'],after_completed=after['completed'],required=after['required'],before_stop=before['stop'],after_stop=after['stop'],before_seconds=before['total_seconds'],after_seconds=after['total_seconds'],batches=after['batches'],commits=after['commits'],extra_transactions=[dict(index=e['index'],committed=e['committed'],selected=len(e['selection']['requested_connection_ids']),primary=e['joint_status'],expansion=None if e['owner_repair'] is None else e['owner_repair']['status'],swap=None if e['owner_swap'] is None else e['owner_swap']['status']) for e in events if e['index']>8]))
assert all(sha(p)==h for p,h in bindings.items());(new/'transaction_limit_diagnosis.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Post-outcome authenticated development limit ablation. Not full physical/native audit, statistical or unseen-family evidence, equal-work comparison, or an end-to-end gain claim.'),indent=2)+'\n')
for row in rows:print(json.dumps(row),flush=True)
