"""Authenticate all snapshot labels; channel-only overflow differs from full RR counts."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha1_cold_iteration_routes_v1_2026-10-10';A=D/'snapshot_audits_v2';p=A/'verification.json';proof=json.loads(p.read_text());assert proof['all_18_snapshot_physical_queries_branch_XML_union_and_log_counts_pass']
bindings={**proof['bindings'],str(p):sha(p),str(Path(__file__)):sha(Path(__file__))};assert all(sha(k)==h for k,h in bindings.items())
assert [r['iteration'] for r in proof['rows']]==list(range(1,19)) and all(r['physical_connections']==6273 for r in proof['rows'])
cp=R/'experiments/sha1_frozen_hotspots_v2_2026-10-10/sha1/comparison.json';comparison=json.loads(cp.read_text())
assert all(sha(k)==h for k,h in comparison['bindings'].items());bindings.update(comparison['bindings']);bindings[str(cp)]=sha(cp)
vp=R/'experiments/sha1_frozen_hotspots_v2_2026-10-10/sha1/comparison_vectors.json';bindings[str(vp)]=sha(vp);vectors=json.loads(vp.read_text());channels=vectors['channels'];assert len({c['node'] for c in channels})==len(channels) and all(c['capacity']>0 for c in channels)
rows=[]
for row in proof['rows']:
 ap=A/f"iteration_{row['iteration']:03d}.json";assert sha(ap)==bindings[str(ap)];a=json.loads(ap.read_text());occ=a['node_occupancy']
 over=sum(occ.get(str(c['node']),0)>c['capacity'] for c in channels);excess=sum(max(0,occ.get(str(c['node']),0)-c['capacity']) for c in channels)
 assert over==row['overused_channel_nodes'] and excess<=row['overflow_units']
 rows.append(dict(**row,channel_overflow_units=excess))
assert rows[-1]['channel_overflow_units']==0
scope='All18 cold snapshots authenticated as printed physical perNET occupation labels, including known illegal congested intermediate states. Not canonical/FULL legal checkpoints, route-failure examples, heldout families, or preregistered transient accuracy evidence. Frozen original metric protocol covers final legal occupancy only; subsequent transient comparisons must be labeled exploratory, use all rounds and retain immutable models.'
assert all(sha(k)==h for k,h in bindings.items())
(D/'transient_label_summary_v2.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,positive_capacity_channel_universe=len(channels),snapshot_physical_label_audit_pass=True,captured_receipt_snapshot_audit_flag_remains_historical_false=True,scope=scope),indent=2)+'\n')
print('PASS all18 transient channel labels',len(channels));print(json.dumps(rows[0]));print(json.dumps(rows[-1]))
