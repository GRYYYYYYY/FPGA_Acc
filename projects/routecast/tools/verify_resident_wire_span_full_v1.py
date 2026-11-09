"""Authenticate fresh wire-span full cohort; native full scope and fixed cold quality gates."""
import sys,json,re
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_route_audit import audit
from audit_native_route import NET
out=R/'experiments/resident_wire_span_full_v1_2026-10-08';rp=out/'receipt.json';data=json.loads(rp.read_text());assert all(sha(k)==v for k,v in data['bindings'].items());bindings={**closure([Path(__file__)]),str(rp):sha(rp)};rows=[]
for row in data['rows']:
 name=row['name'];assert row['status']=='COMPLETE_WORKFLOW_CANONICAL_PASS';w=out/name;assert all(sha(k)==v for k,v in row['files'].items());assert all(sha(k)==v for k,v in row['canonical']['files'].items())
 ref=R/'experiments/resident_wire_span_cohort_v1_2026-10-07'/name
 for f in ['endpoints.json','resident/floors.json','resident/initial.json','resident/sketch.json']:
  assert json.loads((w/f).read_text())==json.loads((ref/f).read_text());bindings[str(ref/f)]=sha(ref/f)
 for i in range(2):
  a=json.loads((w/f'resident/round{i}.json').read_text());b=json.loads((ref/f'resident/round{i}.json').read_text());assert a==b
 ep=json.loads((w/'endpoints.json').read_text());a=audit(Path(ep['inputs']['graph']['path']),w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()));assert actual==required and a['overflow_units']==0
 for file in [w/'native.log',out/(name+'_canonical')/'reload.log']:
  text=file.read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text;assert float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])==row['cpd_ns']
 assert row['canonical']['mismatches']==row['canonical']['fixups']==0
 cp=R/'experiments/frisc_resident_full_cold_v2_2026-10-07/receipt.json' if name=='frisc' else R/'experiments/resident_full_cold_v1_2026-10-07/receipt.json';cold=next(r for r in json.loads(cp.read_text())['rows'] if r['name']==name);bindings[str(cp)]=sha(cp)
 rows.append(dict(name=name,connections=len(ep['connections']),seed_cpd_ns=row['cpd_ns'],seed_wirelength=row['wirelength'],reference_cold_cpd_ns=cold['cpd_ns'],reference_cold_wirelength=cold['wirelength'],quality_against_archived_cold_pass=row['cpd_ns']<=cold['cpd_ns'] and row['wirelength']<=cold['wirelength'],actual_full_seconds=row['actual_complete_workflow_seconds']))
(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'fresh_estimates_native_full_endpoints_capacity_canonical_pass':True,'fresh_paired_cold_done':False,'heldout_family':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
