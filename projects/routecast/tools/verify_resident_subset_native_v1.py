"""Independent seed/final printed branches, original endpoint coverage and native log audit."""
import sys,json,re
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from audit_native_route import NET
from stream_native_route_audit import audit
out=R/'experiments/resident_subset_native_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};rows=[]
for row in r['rows']:
 name=row['name'];bindings.update(row['files']);assert all(sha(k)==h for k,h in bindings.items());w=out/name;epfile=R/f'experiments/mcnc_fresh_conversion_resident_v1_2026-10-07/{name}/endpoints.json';ep=json.loads(epfile.read_text());subset=json.loads((R/f'experiments/resident_native_seed_subset_v1_2026-10-07/{name}/subset.json').read_text());graph=Path(ep['inputs']['graph']['path']);assert row['identity_exit_code']==1;assert row['native_exit_code']==0 and row['native_status']=='SEEDED_FULL_STA_ENDPOINT_CAPACITY_PASS';table={x['name']:x for x in map(json.loads,(w/'identity.jsonl').read_text().splitlines())};pins=json.loads((w/'bindings.json').read_text());assert set(pins)=={str(x['connection_id']) for x in subset['records']}
 for rec in subset['records']:
  binding=pins[str(rec['connection_id'])];native=table[ep['net_names'][str(rec['net_id'])]];assert binding['net']==native['net_id'] and binding['name']==native['name'];assert binding['pin'] in {x['index'] for x in native['pins'] if x['index']>0}
 log=(w/'native.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log;imported=re.findall(r'NET-aware seed imported feasible=(\d)',log);assert imported;cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log);wire=re.findall(r'Total wirelength:\s*(\d+)',log);assert float(cpd[-1])==row['cpd_ns'] and int(wire[-1])==row['wirelength']
 for filename,records in [('seed.route',subset['records']),('output.route',ep['connections'])]:
  file=w/filename;a=audit(graph,file);names={int(m[1]):m[2] for line in file.read_text().splitlines() if (m:=NET.match(line))};expected=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in records);actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()));assert expected==actual;assert a['overflow_units']==0
  assert 'Placement_ID: SHA256:'+sha(w/'design.place') in file.read_text().splitlines()[0]
 rows.append(dict(name=name,retained_connections=len(subset['records']),all_original_connections=len(ep['connections']),seed_import_capacity_feasible=bool(int(imported[-1])),native_cpd_ns=row['cpd_ns'],native_wirelength=row['wirelength'],native_seconds=row['native_seconds'],subset_native_stage_seconds=row['actual_subset_native_stage_seconds']));print('PASS native seed/final FULL scope',name,len(ep['connections']),bool(int(imported[-1])),flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_seed_and_final_endpoint_occurrences_native_FULL_STA_and_capacity_pass=True,scope='Seed node-capacity and all original endpoint occurrence coverage with actual native FULL/STA logs. Not original proxy-budget checkpoint, canonical source/post-routed NET reload or fresh cold QoR/net-gain/heldout proof.'),indent=2)+'\n')
