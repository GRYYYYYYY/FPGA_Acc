"""Evaluate existing two-family evidence completeness, no retrospective deployment."""
import json,hashlib,shutil
from pathlib import Path
from fractions import Fraction
from native_feedback_admission import decide
from pre_route_endpoints import sha

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/rc_feedback_admission_audit_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('audit_rc_feedback_admission.py','native_feedback_admission.py','pre_route_endpoints.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 reports=[]
 for folder in ('multiplier_cw32_rc_budget_pressure_trial_2026-10-06','constant_multiplier_cw32_rc_budget_pressure_trial_2026-10-06'):
  parent=root/'experiments'/folder;pr=json.loads((parent/'receipt.json').read_text());assert sha(parent/'protocol.json')==pr['protocol_sha256']
  for name,identity in pr['case_receipts'].items():
   d=parent/name;assert sha(d/'receipt.json')==identity;case=json.loads((d/'receipt.json').read_text());assert sha(d/'inputs.json')==case['inputs_sha256'];inp=json.loads((d/'inputs.json').read_text());assert all(sha(v['path'])==v['sha256'] for v in inp['inputs'].values());context=hashlib.sha256(json.dumps(inp['inputs'],sort_keys=True).encode()).hexdigest();scope=hashlib.sha256(b'actual measurement scope: native route only; no per-case complete pipeline measurement').hexdigest();off=next(r for r in case['rows'] if r['mode']=='off');on=next(r for r in case['rows'] if r['mode']=='on');baseline={'success':off['success'],'physical_verified':off['independent_physical_pass'] is True,'context_sha256':context,'timing_scope_sha256':scope};candidate={**baseline,'success':on['success'],'physical_verified':on['independent_physical_pass'] is True,'cpd_ns':Fraction(str(on['cpd_ns'])) if on['cpd_ns'] is not None else None,'wirelength':on['wirelength'],'full_pipeline_s':None,'route_sha256':on['route_sha256'],'measurement_receipt_sha256':identity}
   # Failed baselines have no certified QoR/time limits: placeholders are not budgets.
   limits={'cpd_limit':Fraction(str(off['cpd_ns'])) if off['cpd_ns'] is not None else Fraction(0),'wirelength_limit':off['wirelength'] if off['wirelength'] is not None else 0,'pipeline_limit':Fraction(0)};result=decide(baseline,candidate,**limits);assert result['status']!='ACCEPT';reports.append({'family_folder':folder,'design':name,'decision':result,'per_case_pipeline_budget_available':False,'limits_scope':'baseline CPD/WL only for successful off; no per-case complete-time budget evidence; zero placeholder does not authorize deployment','measurement_receipt_sha256':identity})
 (out/'report.json').write_text(json.dumps(reports,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'Post-outcome evidence audit, not prospective admission calibration or accepted repair. Caller still authenticates actual native evidence; gate alone is no file/process atomic publication.'},indent=2)+'\n');print(json.dumps({'cases':len(reports),'accept':0,'insufficient_baseline':sum(r['decision']['status']=='INSUFFICIENT_BASELINE' for r in reports),'reject':sum(r['decision']['status']=='REJECT' for r in reports)}))
if __name__=='__main__':main()
