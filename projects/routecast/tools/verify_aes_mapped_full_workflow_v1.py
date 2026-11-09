"""Authenticate fresh wire-span full cohort; native full scope and fixed cold quality gates."""
import sys,json,re
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_route_audit import audit
from audit_native_route import NET
out=R/'experiments/aes_mapped_full_workflow_v1_2026-10-08';rp=out/'receipt.json';data=json.loads(rp.read_text());assert all(sha(k)==v for k,v in data['bindings'].items());bindings={**closure([Path(__file__)]),str(rp):sha(rp)};rows=[]
for row in data['rows']:
 name=row['name'];assert row['status']=='COMPLETE_WORKFLOW_CANONICAL_PASS';w=out/name;assert all(sha(k)==v for k,v in row['files'].items());assert all(sha(k)==v for k,v in row['canonical']['files'].items())
 ref=R/'experiments/aes_frozen_estimates_v1_2026-10-08'/name
 assert json.loads((w/'endpoints.json').read_text())==json.loads((R/'experiments/aes_rr_graph_only_v1_2026-10-08'/name/'endpoints.json').read_text())
 for f in ['resident/floors.json','resident/initial.json','resident/sketch.json']:
  assert json.loads((w/f).read_text())==json.loads((ref/f).read_text());bindings[str(ref/f)]=sha(ref/f)
 for i in range(2):
  a=json.loads((w/f'resident/round{i}.json').read_text());b=json.loads((ref/f'resident/round{i}.json').read_text());assert a==b
 ep=json.loads((w/'endpoints.json').read_text());a=audit(Path(ep['inputs']['graph']['path']),w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()));assert actual==required and a['overflow_units']==0
 for file in [w/'native.log',out/(name+'_canonical')/'reload.log']:
  text=file.read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text;assert float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])==row['cpd_ns']
 assert row['canonical']['mismatches']==row['canonical']['fixups']==0
 rows.append(dict(name=name,connections=len(ep['connections']),seed_cpd_ns=row['cpd_ns'],seed_wirelength=row['wirelength'],actual_full_seconds=row['actual_complete_workflow_seconds']))
(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'fresh_estimates_native_full_endpoints_capacity_canonical_pass':True,'fresh_paired_cold_done':False,'originalHDL_semantic_relation_proven':False,'mapped_candidate_scope_only':True},indent=2)+'\n');print(json.dumps(rows,indent=2))
