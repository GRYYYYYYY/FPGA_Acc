"""Current full-domain loader and wrong-epoch/endpoint rejection checks."""
from pathlib import Path
import json,hashlib,tempfile
from load_initial_connection_criticalities_v3 import load
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 O=R/'experiments/mmc_current_initial_timing_loader_contract_v3_2026-10-19';O.mkdir(exist_ok=False);B=R/'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19';rows=[];bindings={};rejected=[]
 for i in range(1,4):
  case=f'episode_{i:02d}';d=B/case;values=load(d);assert set(values)==set(range(115572));records=json.loads((d/'initial_connection_criticalities.json').read_text())
  for r in records:
   v=values[r['connection_id']];assert v['criticality_numerator']/v['criticality_denominator']==v['criticality'] and 0<=v['criticality']<=1
  try:values[0]['criticality']=0
  except TypeError:pass
  else:raise AssertionError('mutable loaded record')
  rows.append({'case':case,'loaded':len(values),'readonly_records':True,'min':min(v['criticality'] for v in values.values()),'max':max(v['criticality'] for v in values.values())})
  for p in [d/'verification.json',d/'initial_connection_criticalities.json']:bindings[str(p)]=sha(p)
 base=json.loads((B/'episode_01/verification.json').read_text());payload=(B/'episode_01/initial_connection_criticalities.json').read_bytes()
 for fault in ['wrong_epoch','wrong_endpoint','false_legacy_equality']:
  with tempfile.TemporaryDirectory(dir=O) as name:
   d=Path(name);p=d/'initial_connection_criticalities.json';p.write_bytes(payload);admission=json.loads(json.dumps(base));admission['bindings'][str(p.resolve())]=sha(p)
   if fault=='wrong_epoch':admission['source_case']='episode_02'
   elif fault=='wrong_endpoint':admission['after_endpoint']=str(R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_02/demand/endpoints.json');admission['bindings'][admission['after_endpoint']]=sha(admission['after_endpoint'])
   else:admission['all_values_and_pin_identities_equal_v1']=True
   (d/'verification.json').write_text(json.dumps(admission));caught=None
   try:load(d)
   except ValueError as e:caught=str(e)
   assert caught is not None;rejected.append({'fault':fault,'error':caught})
 for p in [Path(__file__).resolve(),R/'tools/load_initial_connection_criticalities_v3.py',B/'independent_verification_v1.json']:bindings[str(p)]=sha(p)
 (O/'verification.json').write_text(json.dumps({'status':'ALL3_CURRENT115572_LOADER_AND_WRONG_EPOCH_ENDPOINT_LEGACY_FLAGS_REJECTION_PASS','rows':rows,'rejections':rejected,'bindings':bindings,'scope':'Native initialized timing admission only. No consumer integration, model/predictor or native policy gain yet.'},indent=2)+'\n');print('CURRENT_TIMING_LOADER3_PASS',rows,rejected,flush=True)
if __name__=='__main__':main()
