"""Independently merge retained/recomputed paths, replay arcs and net unions."""
from collections import Counter
import hashlib,json
from pathlib import Path
from rr_graph import read_rr_graph
from physical_prediction_audit import audit

root=Path('experiments/moved_net_trial_2026-10-04');proto=json.loads((root/'protocol.json').read_text());receipt=json.loads((root/'receipt.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if receipt['protocol_sha256']!=sha(root/'protocol.json'):raise ValueError('protocol changed')
for entry in proto['inputs'].values():
    if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
ep=json.loads(Path(proto['inputs']['endpoints']['path']).read_text());change=json.loads(Path(proto['inputs']['change']['path']).read_text())
old=json.loads(Path(proto['inputs']['old_paths']['path']).read_text());partial=json.loads((root/'partial.json').read_text());fresh=json.loads((root/'fresh.json').read_text())
expected=set(change['affected_complete_net_connection_ids']);recomputed={r['connection_id']:r for r in partial['connections']}
if set(recomputed)!=expected:raise ValueError('recomputed cohort mismatch')
merged={r['connection_id']:{**r,'method':'retained'} for r in old['connections']}
for cid,r in recomputed.items():merged[cid]={**r,'method':'recomputed'}
full={r['connection_id']:r for r in fresh['connections']}
fields=('connection_id','net_id','source','sink','physical_edge_ids')
if set(merged)!=set(full) or any(tuple(merged[c][k] for k in fields)!=tuple(full[c][k] for k in fields) for c in merged):raise ValueError('incremental paths differ from full rebuild')
pred={'physical_graph_sha256':fresh['physical_graph_sha256'],'connections':list(merged.values()),'node_occupancy':fresh['node_occupancy'],'methods':dict(Counter(r['method'] for r in merged.values())),'completed':len(merged),'requested':len(merged)}
g=read_rr_graph(proto['inputs']['graph']['path']);report=audit(g,ep,pred)
report.update(protocol_sha256=sha(root/'protocol.json'),auditor_sha256=sha(__file__),artifacts={n:sha(root/n) for n in ('partial.json','fresh.json','receipt.json')},independent_merge_matches_full_paths=True)
(root/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
