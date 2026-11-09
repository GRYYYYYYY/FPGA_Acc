"""Authenticated development ablation summary, not native QoR or a speedup proof."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
old=R/'experiments/mcnc_pending_swap_worker_cache_v20_2026-10-07';new=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07'
a=json.loads((old/'protocol.json').read_text());b=json.loads((new/'protocol.json').read_text())
assert a['cases']==b['cases'] and all(b['inputs'].get(k)==h for k,h in a['inputs'].items())
assert set(b['inputs'])-set(a['inputs'])=={str(R/'experiments/dsip_observer_joint_pair_v2_2026-10-07/receipt.json')}
assert a['policy']==b['policy']
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
 previous=json.loads((old/name/'candidate.json').read_text());current=json.loads((new/name/'candidate.json').read_text())
 rows.append(dict(before_cache_build_and_archive_seconds=before['cache_summary']['build_and_archive_seconds'],after_cache_build_and_archive_seconds=after['cache_summary']['build_and_archive_seconds'],before_cache_construction_seconds=before['cache_summary']['construction_seconds'],after_cache_construction_seconds=after['cache_summary']['construction_seconds'],worker_restarts=after['cache_summary']['worker_restarts'],exact_reference_records=previous['records']==current['records'],exact_reference_ledger=previous['ledger']==current['ledger'],name=name,before_completed=before['completed'],after_completed=after['completed'],required=after['required'],before_stop=before['stop'],after_stop=after['stop'],before_seconds=before['total_seconds'],after_seconds=after['total_seconds'],batches=after['batches'],commits=after['commits'],extra_transactions=[dict(index=e['index'],committed=e['committed'],selected=len(e['selection']['requested_connection_ids']),primary=e['joint_status'],expansion=None if e['owner_repair'] is None else e['owner_repair']['status'],swap=None if e['owner_swap'] is None else e['owner_swap']['status']) for e in events if e['index']>8]))
assert all(sha(p)==h for p,h in bindings.items());(new/'observer_clone_comparison.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Post-outcome authenticated cache implementation comparison. Identical algorithm policy and design inputs; same worker backend; additional paired observer-clone proof frozen; single independent runs with deadlines and uncontrolled host load. Not full physical/native audit, statistical or unseen-family evidence, equal-work comparison, or an end-to-end gain claim.'),indent=2)+'\n')
for row in rows:print(json.dumps(row),flush=True)
