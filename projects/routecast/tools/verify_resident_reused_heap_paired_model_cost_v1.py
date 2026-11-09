"""Authenticate each full model run and independently recompute paired ratios."""
import json,sys,math,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
name=sys.argv[1];assert name in ('8051','xtea')
D=R/'experiments/resident_reused_heap_paired_model_cost_v1_2026-10-08'/name
reference=R/'experiments/freecores_resident_v1_2026-10-08'/name/'resident'
bindings={str(Path(__file__)):sha(Path(__file__))}
def load(p):
 d=json.loads(p.read_text());bindings[str(p)]=sha(p)
 for section in ('bindings','files'):
  for k,h in d.get(section,{}).items():
   if k in bindings:assert bindings[k]==h,k
   bindings[k]=h
 return d
p=load(D/'protocol.json');r=load(D/'receipt.json');ref=load(reference/'receipt.json');assert p['name']==name and not r['whole_native_workflow_gain_proven']
expected=[(i,mode) for i,pair in enumerate(p['pairs']) for mode in pair]
assert p['pairs']==[['baseline','candidate'],['candidate','baseline'],['baseline','candidate']]
assert [(x['pair'],x['mode']) for x in r['rows']]==expected and len(expected)==6
ref_hashes={f:sha(reference/f) for f in ('floors.json','initial.json','round0.json','round1.json','sketch.json')}
for f,h in ref_hashes.items():bindings[str(reference/f)]=h
for row in r['rows']:
 assert row['status']=='FULL_MODEL_PARITY_PASS' and math.isfinite(row['model_subprocess_seconds']) and row['model_subprocess_seconds']>0
 arm=D/(str(row['pair'])+'_'+row['mode']);a=load(arm/'receipt.json');assert len(a['rounds'])==len(ref['rounds'])==2
 for f,h in ref_hashes.items():assert sha(arm/f)==h;bindings[str(arm/f)]=h
 for x,y in zip(a['rounds'],ref['rounds']):
  assert set(x)==set(y)
  for key in y:
   if key not in ('seconds','state_file'):assert x[key]==y[key],key
 source=R/'tools'/('run_resident_soft_demand_affected_cache_v1.py' if row['mode']=='baseline' else 'run_resident_soft_demand_reused_heap_v2.py');assert a['bindings'][str(source)]==sha(source)
ratios=[]
for pair in range(3):
 seconds={x['mode']:x['model_subprocess_seconds'] for x in r['rows'] if x['pair']==pair};ratios.append(seconds['candidate']/seconds['baseline'])
assert ratios==r['paired_ratios'] and statistics.median(ratios)==r['median_model_ratio']
assert all(sha(k)==h for k,h in bindings.items())
result=dict(bindings=bindings,name=name,all_six_full_state_and_feedback_event_outputs_authenticated=True,paired_ratios=ratios,median_model_ratio=statistics.median(ratios),all_observed_candidate_runs_faster=all(v<1 for v in ratios),whole_native_workflow_gain_proven=False,scope='Full model output and ratio arithmetic authentication; wall intervals reported by frozen producer, not independently reconstructed. Three alternating-order pairs, known case, validation after timer excluded, no dedicated-host/statistical stability/native full-workflow/heldout/hardware inference.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(name,ratios,'median',statistics.median(ratios),'all faster',result['all_observed_candidate_runs_faster'])
