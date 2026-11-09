"""Independently replay current cold comparison logs, fixed-input hashes and endpoints."""
import sys,json,re
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from stream_native_route_audit import audit
from audit_native_route import NET
from source_binding_v2 import closure
out=R/'experiments/resident_subset_fresh_cold_v1_2026-10-07';p=out/'receipt.json';data=json.loads(p.read_text());src=R/'experiments/resident_subset_native_v1_2026-10-07';candidate=json.loads((src/'receipt.json').read_text());old={r['name']:r for r in candidate['rows']}
bindings={**closure([Path(__file__)]),str(p):sha(p),str(src/'receipt.json'):sha(src/'receipt.json')};rows=[]
assert all(sha(k)==v for k,v in data['bindings'].items())
for row in data['rows']:
 name=row['name'];w=out/name;c=old[name];assert row['command']==c['command']
 for f in ['design.blif','design.net','design.place']:assert sha(w/f)==sha(src/name/f)==c['files'][str(src/name/f)]
 for record in [row,row['canonical']]:assert all(sha(k)==v for k,v in record['files'].items())
 log=(w/'native.log').read_text();reload=(out/(name+'_canonical')/'reload.log').read_text();assert 'NET-aware seed imported' not in log
 for text in [log,reload]:assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
 assert re.search(r'Found 0 mismatches',reload) and re.search(r'Fixed 0 routing traces',reload)
 cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);wire=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);assert cpd==row['cpd_ns']==row['canonical']['cpd_ns'] and wire==row['wirelength']
 epfile=R/f'experiments/mcnc_fresh_conversion_resident_v1_2026-10-07/{name}/endpoints.json';assert sha(epfile)==candidate['bindings'][str(epfile)];ep=json.loads(epfile.read_text());bindings[str(epfile)]=sha(epfile)
 graph=Path(ep['inputs']['graph']['path']);a=audit(graph,w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()));assert required==observed and a['overflow_units']==0
 passed=c['cpd_ns']<=cpd and c['wirelength']<=wire;assert passed==row['candidate_quality_gate_pass']
 rows.append(dict(name=name,cold_cpd_ns=cpd,seed_cpd_ns=c['cpd_ns'],cold_wirelength=wire,seed_wirelength=c['wirelength'],quality_gate_pass=passed,cold_native_seconds=row['native_seconds'],seed_native_seconds=c['native_seconds']))
(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'same_fixed_inputs_native_full_canonical_and_endpoint_capacity_pass':True,'complete_workflow_gain_verified':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
