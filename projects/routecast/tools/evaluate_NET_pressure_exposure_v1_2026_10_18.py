"""Frozen540 NET ranking/captured-operation diagnostic cells."""
import hashlib,json,math
from array import array
from pathlib import Path
from pressure_rank_metrics_v1 import top,metric

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(info):
 assert sha(info['path'])==info['sha256'];a=array(info.get('typecode','d'));a.frombytes(Path(info['path']).read_bytes());assert len(a)==info['values'];return a

def main():
 source=Path('experiments/mmc_NET_pressure_exposure_v1_2026-10-18');target=Path('experiments/mmc_NET_pressure_targets_v1_2026-10-18');vp=Path('experiments/mmc_NET_pressure_inputs_verification_v1_2026-10-18/verification.json');v=json.loads(vp.read_text());assert v['status']=='pass';plan=json.loads((source/'protocol.json').read_text());sm=json.loads((source/'vector_manifest.json').read_text());tm=json.loads((target/'vector_manifest.json').read_text());out=Path('experiments/mmc_NET_pressure_quality_v1_2026-10-18');out.mkdir(exist_ok=False)
 bindings={**v['bindings'],str(vp.resolve()):sha(vp),str(Path(__file__).resolve()):sha(__file__),str(Path('tools/pressure_rank_metrics_v1.py').resolve()):sha('tools/pressure_rank_metrics_v1.py')}
 for p,h in bindings.items():assert sha(p)==h
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,source_plan=str((source/'protocol.json').resolve()),scope=plan['scope']),f,indent=2)
 rows=[]
 for case in plan['cases']:
  predictions={};pt={}
  for src in plan['sources']:
   for method in plan['methods']:
    ref=case+'__'+src+'__'+method;predictions[ref]=read(sm[ref]);pt[ref]=top(predictions[ref],len(predictions[ref])//20)
  for policy in plan['policies']:
   for label in plan['targets']:
    tref=case+'__'+policy+'__'+label;truth=read(tm[tref]);k=len(truth)//20;tt=top(truth,k);total=sum(truth)
    for src in plan['sources']:
     for method in plan['methods']:
      ref=case+'__'+src+'__'+method;result=metric(predictions[ref],truth,pt[ref],tt);captured=sum(truth[i] for i in pt[ref]['selected']);capture=None if total==0 else captured/total;enrichment=None if capture is None else capture/(k/len(truth))
      rows.append(dict(case=case,policy=policy,target=label,source=src,method=method,prediction_vector=ref,truth_vector=tref,metrics=result,selected_target_count=int(captured),total_target_count=int(total),target_count_capture_fraction=capture,enrichment_over_uniform_selection=enrichment))
  print('NET PRESSURE QUALITY CASE DONE',case,flush=True)
 assert len(rows)==540
 for p,h in bindings.items():assert sha(p)==h
 with (out/'results.json').open('x') as f:json.dump(dict(status='all540_NET_diagnostic_cells_computed_independent_metrics_pending',bindings=bindings,rows=rows,scope=plan['scope']),f,indent=2)
if __name__=='__main__':main()
