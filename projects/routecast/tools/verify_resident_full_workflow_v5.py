"""Audit whole-clock run input binding, fresh estimator parity and native outputs."""
import sys,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/resident_full_workflow_v5_2026-10-07';p=out/'receipt.json';data=json.loads(p.read_text());assert all(sha(k)==v for k,v in data['bindings'].items());bindings={**closure([Path(__file__)]),str(p):sha(p)};rows=[]
for r in data['rows']:
 assert r['status']=='COMPLETE_WORKFLOW_CANONICAL_PASS';name=r['name'];w=out/name
 assert all(sha(k)==v for k,v in r['files'].items());assert all(sha(k)==v for k,v in r['canonical']['files'].items())
 base=R/'experiments/mcnc_fresh_conversion_resident_v1_2026-10-07'/name
 for f in ['endpoints.json','resident/floors.json','resident/initial.json','resident/sketch.json']:
  assert json.loads((w/f).read_text())==json.loads((base/f).read_text());bindings[str(base/f)]=sha(base/f)
 expected=json.loads((R/'experiments/resident_native_seed_subset_v1_2026-10-07'/name/'subset.json').read_text());selected=json.loads((w/'subset.json').read_text());assert selected['records']==expected['records'] and selected['pending']==expected['required_reroute_connection_ids']
 for file in [w/'native.log',out/(name+'_canonical')/'reload.log']:
  text=file.read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
  assert float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])==r['cpd_ns']
 assert r['canonical']['mismatches']==r['canonical']['fixups']==0
 assert all(v>=0 for v in r['stages'].values()) and sum(r['stages'].values())<=r['actual_complete_workflow_seconds']
 rows.append({'name':name,'seconds':r['actual_complete_workflow_seconds'],'stages':r['stages'],'cpd_ns':r['cpd_ns'],'wirelength':r['wirelength']})
(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'bound_files_fresh_estimates_selection_parity_and_native_canonical_pass':True,'matched_fresh_cold_whole_clock_done':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
