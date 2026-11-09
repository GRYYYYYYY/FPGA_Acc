"""Authenticate frisc extension; compare fresh soft state and all native endpoints."""
import sys,json,re
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_route_audit import audit
from audit_native_route import NET
out=R/'experiments/frisc_resident_full_workflow_v2_2026-10-07';p=out/'receipt.json';data=json.loads(p.read_text());assert all(sha(k)==v for k,v in data['bindings'].items());r=data['rows'][0];assert r['status']=='COMPLETE_WORKFLOW_CANONICAL_PASS';assert all(sha(k)==v for k,v in r['files'].items());assert all(sha(k)==v for k,v in r['canonical']['files'].items());w=out/'frisc';ep=json.loads((w/'endpoints.json').read_text());old=R/'experiments/frisc_resident_full_workflow_v1_2026-10-07/frisc';bindings={**closure([Path(__file__)]),str(p):sha(p)}
for f in ['endpoints.json','resident/floors.json','resident/initial.json','resident/sketch.json','subset.json']:
 assert json.loads((w/f).read_text())==json.loads((old/f).read_text());bindings[str(old/f)]=sha(old/f)
graph=Path(ep['inputs']['graph']['path']);a=audit(graph,w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};expected=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()));assert expected==actual and a['overflow_units']==0
for file in [w/'native.log',out/'frisc_canonical/reload.log']:
 log=file.read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log;assert float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1])==r['cpd_ns']
assert r['canonical']['mismatches']==r['canonical']['fixups']==0
(out/'verification.json').write_text(json.dumps({'bindings':bindings,'all_5767_native_endpoints_capacity_and_canonical_pass':True,'fresh_estimate_and_subset_v1_exact_parity':True,'heldout_family':False,'cold_quality_and_full_gain_done':False,'row':r},indent=2)+'\n');print('PASS frisc native/canonical 5767',r['cpd_ns'],r['wirelength'])
