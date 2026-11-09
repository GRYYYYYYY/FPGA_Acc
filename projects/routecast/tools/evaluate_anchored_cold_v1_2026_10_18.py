"""36 frozen primary-cold diagnostic rows, unchanged original gates."""
import hashlib,json
from array import array
from pathlib import Path
from prediction_metrics import compare

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path('experiments/mmc_anchored_cold_quality_v1_2026-10-18');out.mkdir(exist_ok=False)
 verification=Path('experiments/mmc_anchored_NET_forecasts_verification_v1_2026-10-18');vp=verification/'verification.json';v=json.loads(vp.read_text());assert v['status']=='pass';planpath=verification/'frozen_outcome_protocol_v1.json';plan=json.loads(planpath.read_text())
 source=Path('experiments/mmc_anchored_NET_forecasts_v1_2026-10-18');manifest=json.loads((source/'vector_manifest.json').read_text());prior=Path('experiments/mmc_multiplacement_quality_v1_2026-10-18');pr=Path('experiments/mmc_pressure_risk_matrix_v1_2026-10-18');pm=json.loads((pr/'vector_manifest.json').read_text());domains=json.loads((pr/'domains.json').read_text());fullindex={n:i for i,n in enumerate(domains['ids']['all_positive_RR'])}
 bindings={**v['bindings'],str(vp.resolve()):sha(vp),str(planpath.resolve()):sha(planpath),str(Path(__file__).resolve()):sha(__file__),str(Path('tools/prediction_metrics.py').resolve()):sha('tools/prediction_metrics.py')}
 for p,h in bindings.items():assert sha(p)==h
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,frozen_plan=str(planpath.resolve()),scope=plan['scope']),f,indent=2)
 def read(info):
  assert sha(info['path'])==info['sha256'];values=array('d');values.frombytes(Path(info['path']).read_bytes());assert len(values)==info['values'];return values
 rows=[];cases=[]
 for case in plan['cases']:
  base=prior/case;ap=base/'verification.json';audit=json.loads(ap.read_text());assert audit['status']=='pass'
  for p in [base/'vectors.json',base/'comparison.json']:assert sha(p)==audit['bindings'][str(p.resolve())];bindings[str(p.resolve())]=sha(p)
  bindings[str(ap.resolve())]=sha(ap);data=json.loads((base/'vectors.json').read_text());old=json.loads((base/'comparison.json').read_text())['metrics']['cold'];channels=data['channels'];bins=data['bins']
  assert [r['node'] for r in channels]==domains['ids']['channels'];assert [r['key'] for r in bins]==domains['ids']['spatial']
  truths=dict(concrete={r['node']:r['labels']['cold']/r['capacity'] for r in channels},spatial={tuple(r['key']):r['labels']['cold']/r['capacity'] for r in bins});methods={}
  for source_name in plan['sources']:
   method='anchored_group_mean__'+source_name;full=read(manifest[case+'__'+source_name+'__anchored_group_mean']);spatial=read(pm[case+'__'+source_name+'__spatial']);preds=dict(concrete={r['node']:full[fullindex[r['node']]] for r in channels},spatial={tuple(r['key']):spatial[i] for i,r in enumerate(bins)})
   methods[method]={}
   for domain in plan['cold']['domains']:
    metrics=compare(preds[domain],truths[domain],20 if domain=='spatial' else max(1,len(channels)//20));methods[method][domain]=metrics;rows.append(dict(case=case,source=source_name,method=method,domain=domain,metrics=metrics))
  candidate=methods[plan['cold']['primary']];checks=[]
  for control in ['previous_native','raw_min_on','native_retained_on']:
   values=[]
   for domain in ['concrete','spatial']:
    for key in ['spearman','precision_at_k']:
     a,b=candidate[domain][key],old[control][domain][key];eps=1e-12 if key=='spearman' else 0
     values.append(dict(domain=domain,metric=key,candidate=a,reference=b,nonregression=a is not None and b is not None and a>=b-eps,strict_improvement=a is not None and b is not None and a>b+eps))
   checks.append(dict(control=control,original_primary_control=control!='native_retained_on',pass_gate=all(r['nonregression'] for r in values) and any(r['strict_improvement'] for r in values),comparisons=values))
  cases.append(dict(case=case,primary_checks=checks,original_primary_gate_pass=all(r['pass_gate'] for r in checks if r['original_primary_control'])));print('ANCHORED COLD ROWS DONE',case,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 assert len(rows)==36
 with (out/'results.json').open('x') as f:json.dump(dict(status='all36_cold_rows_computed_independent_metrics_pending',bindings=bindings,rows=rows,cases=cases,scope=plan['scope']),f,indent=2)
if __name__=='__main__':main()
