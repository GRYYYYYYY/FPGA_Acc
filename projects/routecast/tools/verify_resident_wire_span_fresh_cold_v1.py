"""Independently audit fresh frisc cold endpoints and same-input quality/full-clock comparison."""
import sys,json,re
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_route_audit import audit
from audit_native_route import NET
out=R/'experiments/resident_wire_span_fresh_cold_v1_2026-10-08';src=R/'experiments/resident_wire_span_full_v1_2026-10-08';rp=out/'receipt.json';sp=src/'receipt.json';cold=json.loads(rp.read_text());seed=json.loads(sp.read_text())
for data in [cold,seed]:
 assert all(sha(k)==v for k,v in data['bindings'].items())
 for row in data['rows']:
  assert all(sha(k)==v for k,v in row['files'].items());assert all(sha(k)==v for k,v in row['canonical']['files'].items())
rows=[]
for c in cold['rows']:
 name=c['name']
 s=next(r for r in seed['rows'] if r['name']==name);assert c['status']=='COLD_NATIVE_AND_CANONICAL_PASS' and s['status']=='COMPLETE_WORKFLOW_CANONICAL_PASS';w=out/name
 for f in ['design.blif','design.net','design.place','endpoints.json']:assert sha(w/f)==sha(src/name/f)
 expected=s['canonical']['command'].copy();expected[0]=str(R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr');expected[expected.index('--analysis')]='--route';expected[expected.index('--route_file')+1]='output.route';assert c['command']==expected
 for root,row in [(out,c),(src,s)]:
  log=(root/name/'native.log').read_text();reload=(root/(name+'_canonical')/'reload.log').read_text()
  assert ('NET-aware seed imported' in log)==(root==src)
  for text in [log,reload]:assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
  assert float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1])==row['cpd_ns']==row['canonical']['cpd_ns'];assert int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1])==row['wirelength'];assert row['canonical']['mismatches']==row['canonical']['fixups']==0
  assert sum(row['stages'].values())<=row['actual_complete_workflow_seconds']
 ep=json.loads((w/'endpoints.json').read_text());a=audit(Path(ep['inputs']['graph']['path']),w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()));assert required==actual and a['overflow_units']==0
 quality=s['cpd_ns']<=c['cpd_ns'] and s['wirelength']<=c['wirelength'];assert quality==c['candidate_quality_gate_pass'];row=dict(name=name,cold_cpd_ns=c['cpd_ns'],seed_cpd_ns=s['cpd_ns'],cold_wirelength=c['wirelength'],seed_wirelength=s['wirelength'],quality_gate_pass=quality,cold_full_seconds=c['actual_complete_workflow_seconds'],seed_full_seconds=s['actual_complete_workflow_seconds'],seed_to_cold_ratio=s['actual_complete_workflow_seconds']/c['actual_complete_workflow_seconds'],cold_native_seconds=c['native_seconds'],seed_native_seconds=s['stages']['native'],connections=len(ep['connections']))
 rows.append(row)
(out/'verification.json').write_text(json.dumps({'bindings':{**closure([Path(__file__)]),str(rp):sha(rp),str(sp):sha(sp)},'all_endpoints_capacity_fixed_inputs_native_and_canonical_pass':True,'heldout_family':False,'single_noninterleaved_run':True,'rows':rows},indent=2)+'\n');print(json.dumps(rows,indent=2))
