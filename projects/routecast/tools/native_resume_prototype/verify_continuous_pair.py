"""Authenticate continuous clocks, feedback and identical target quality evidence."""
import json,sys
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'experiments/native_resume_continuous_pair_2026-10-07';tp=base/'timers.json';timers=json.loads(tp.read_text());bindings={str(tp):sha(tp),str(Path(__file__)):sha(Path(__file__))};receipts={};protocols={}
assert sha(Path(__file__).with_name('continuous_cost_trial.py'))==timers['producer_sha256']
for row in timers['rows']:
 mode=row['mode'];assert row['exit_code']==0 and sha(base/f'{mode}.log')==row['log_sha256']
 work=ROOT/f'experiments/native_resume_continuous_{mode}_2026-10-07';rp=work/'receipt.json';pp=work/'protocol.json';r,p=json.loads(rp.read_text()),json.loads(pp.read_text())
 assert r['protocol_sha256']==sha(pp)
 for mapping in (r['files'],p['inputs'],p['sources'],r['canonical']['files']):
  for file,digest in mapping.items():assert sha(file)==digest;bindings[file]=digest
 assert r['canonical']['mismatches']==r['canonical']['fixups']==0 and r['all_target_endpoints_match'] and r['raw_canonical_paths_preserved'] and r['physical_audit']['overflow_units']==0
 assert sum(s['seconds'] for s in r['stages'])<=r['internal_seconds']<=row['external_seconds']
 for stage in r['stages']:
  if 'native' in stage:assert stage['native']['exit_code']==0
 bindings[str(rp)]=sha(rp);bindings[str(pp)]=sha(pp);receipts[mode]=r;protocols[mode]=p
w,c=receipts['workflow'],receipts['cold'];assert w['feedback']==next(s['decision'] for s in w['stages'] if s['stage']=='feedback_decision')
assert w['feedback']['net']=='y3_7' and w['feedback']['eligible'] and w['selected_work'].endswith('/second')
assert len([s for s in w['stages'] if 'native' in s])==2 and len([s for s in c['stages'] if 'native' in s])==1
shared=set(protocols['workflow']['inputs'])&set(protocols['cold']['inputs']);assert all(protocols['workflow']['inputs'][p]==protocols['cold']['inputs'][p] for p in shared)
for suffix in ('target_endpoints.json','target.place','design.net','design.blif','rr_graph.xml'):assert any(p.endswith(suffix) for p in shared)
norm=lambda p:{n:Counter(paths) for n,paths in physical_paths(p).items() if paths}
reference=ROOT/'experiments/native_resume_critical_release_v7_2026-10-07/resume/canonical/design.route'
assert norm(ROOT/'experiments/native_resume_continuous_workflow_2026-10-07/canonical/design.route')==norm(reference);bindings[str(reference)]=sha(reference)
t={r['mode']:r['external_seconds'] for r in timers['rows']}
joint=F(w['cpd_ns'])<=F(c['cpd_ns']) and w['wirelength']<=c['wirelength']
result=dict(bindings=bindings,workflow_external_seconds=t['workflow'],cold_external_seconds=t['cold'],workflow_over_cold_ratio=t['workflow']/t['cold'],joint_nonregression=joint,candidate_cpd_ns=w['cpd_ns'],cold_cpd_ns=c['cpd_ns'],candidate_wirelength=w['wirelength'],cold_wirelength=c['wirelength'],net_time_gain=t['workflow']<t['cold'],candidate_paths_match_development_reference=True,scope='Serial single prepared-input observations; OS caches not reset. All initial mapping/oldseed/endpoint/RR production/compile excluded equally and explicitly; workflow pays two attempts, feedback, seed conversion and selected final proofs; cold pays fresh route and same canonical/physical/endpoint proof. Cold read only for evaluation after strategy selection, not oracle admission. Source closure/hash/proof costs included. Not heldout, stable performance, original-input end-to-end or durable live publication.')
(base/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='bindings'})
