"""Identity-only join of baseline route timing to original packed endpoints."""
import json, math
from pathlib import Path
from pre_route_endpoints import sha
root=Path('experiments/baseline_cluster_criticality_v7_2026-10-04')
mp=Path('experiments/pre_route_endpoints_2026-10-04/diffeq_mapping.json')
ep=Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json')
raw=root/'routecast_cluster_criticality.jsonl'
rows=[json.loads(x) for x in raw.read_text().splitlines()]
before=root/'routecast_atom_before.jsonl';after=root/'routecast_atom_after.jsonl'
atom_rows=[json.loads(x) for x in before.read_text().splitlines()]
post_rows=[json.loads(x) for x in after.read_text().splitlines()]
assert atom_rows == post_rows and sha(before)==sha(after)
atoms={r['atom_pin_id']:r for r in atom_rows}
assert len(atoms)==len(atom_rows)
assert all(type(r['atom_pin_id']) is int and type(r['tatum_node']) is int and r['atom_pin_id']>=0 and r['tatum_node']>=0 and math.isfinite(r['criticality']) and 0<=r['criticality']<=1 for r in atom_rows)
for row in rows:
 assert row['atom_pins']
 assert all(a==atoms[a['atom_pin_id']] for a in row['atom_pins'])
 assert row['criticality']==max(a['criticality'] for a in row['atom_pins'])
key=lambda r:(r['net'],r['block'],r['port'],r['bit'])
assert len({key(r) for r in rows})==len(rows)
lookup={key(r):r for r in rows}
m=json.loads(mp.read_text());endpoints=json.loads(ep.read_text())['connections']
excluded={r['net_id'] for r in m['excluded_nets']}
sinks=[r for r in m['pin_details'] if r['role']=='SINK' and r['net_id'] not in excluded]
sinks.sort(key=lambda r:r['net_id'])
assert len(sinks)==len(endpoints)
joined=[]
for pin,e in zip(sinks,endpoints):
 assert pin['net_id']==e['net_id'] and pin['rr_node']==e['sink']
 r=lookup[key(pin)]
 assert r['net_id']==pin['net_id'] and r['atom_pins']
 vals=[a['criticality'] for a in r['atom_pins']]
 assert all(math.isfinite(v) and 0<=v<=1 for v in vals)
 assert math.isfinite(r['criticality']) and abs(r['criticality']-max(vals))<=1e-8
 assert all(a==atoms[a['atom_pin_id']] for a in r['atom_pins'])
 joined.append({**e,'packed_pin':{k:pin[k] for k in ('net','block','port','bit')},'criticality':r['criticality'],'atom_pins':r['atom_pins']})
prior=Path('experiments/baseline_cluster_criticality_v4_2026-10-04')
report_names=['report_timing.setup.rpt','report_timing.hold.rpt','report_unconstrained_timing.setup.rpt','report_unconstrained_timing.hold.rpt']
assert all(sha(root/n)==sha(prior/n) for n in report_names)
artifact={'schema':'ROUTECAST_BASELINE_CLUSTER_CRITICALITY_V1','provenance':'existing baseline route timing before native packed-netlist resync; warm-state research input only, not prospective pre-route prediction','graph_sha256':json.loads(ep.read_text())['graph_sha256'],'inputs':{str(p):sha(p) for p in (raw,mp,ep,before,after)},'connections':joined}
(root/'joined_criticality.json').write_text(json.dumps(artifact,indent=2)+'\n')
summary={'full_atom_pins_compared':len(atom_rows),'before_after_atom_records_exact':True,'max_atom_criticality_delta':0,'all_cluster_atom_references_checked':True,'exported_cluster_sinks':len(rows),'joined_connections':len(joined),'excluded_export_rows':len(rows)-len(joined),'positive_criticality':sum(r['criticality']>0 for r in joined),'max_criticality':max(r['criticality'] for r in joined),'atom_pin_references':sum(len(r['atom_pins']) for r in joined),'unique_tatum_nodes':len({a['tatum_node'] for r in joined for a in r['atom_pins']}),'semantic_pin_keys_unique':True,'cluster_criticality_matches_max_atom':True,'reports_identical_to_native_post_resync_analysis':True,'joined_sha256':sha(root/'joined_criticality.json')}
(root/'identity_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
