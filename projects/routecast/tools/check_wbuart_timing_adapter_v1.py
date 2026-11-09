"""Current-epoch adapter acceptance and stale-frame/epoch rejection contract."""
import hashlib,json
from pathlib import Path
from load_wbuart_current_initial_timing_v1 import load,epoch
R=Path(__file__).resolve().parents[1];T=R/'experiments/wbuart_frame_timings_v1_2026-10-20';O=R/'experiments/wbuart_timing_adapter_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);p=T/'verification.json';v=json.loads(p.read_text());assert len(v['rows'])==12
 for n,h in v['bindings'].items():assert sha(Path(n))==h
 positive=0;negative=0;rows=[]
 for i,row in enumerate(v['rows']):
  d=Path(row['timing_directory']);ep=Path(row['endpoint']);e=epoch(d);vals=load(d,ep,expected_epoch=e);assert len(vals)==2493;positive+=1
  other=Path(v['rows'][(i+1)%12]['endpoint']);assert sha(other)!=sha(ep)
  for label,args in [('wrong_frame',{'endpoint_path':other,'expected_epoch':e}),('wrong_epoch',{'endpoint_path':ep,'expected_epoch':'0'*64})]:
   try:load(d,**args)
   except ValueError:negative+=1
   else:raise AssertionError('Adapter accepted '+label)
  proof=json.loads((d/'verification.json').read_text());assert proof['all_sink_pins']==2566 and proof['ignored_clock_pins']==71 and proof['ignored_nonclock_pins']==2 and proof['atom_rows']==4493;rows.append({'case':row['case'],'connections':len(vals),'epoch':e,'wrong_frame_rejected':True,'wrong_epoch_rejected':True})
 out={'status':'ALL12_CURRENT_TIMING_LOADS_AND24_STALE_FRAME_EPOCH_REJECTIONS_PASS','positive_cases':positive,'negative_cases':negative,'rows':rows,'scope':'Input adapter contract only, no predictor quality/native current routed timing or gain claim.','bindings':{str(p):sha(p) for p in [Path(__file__),R/'tools/load_wbuart_current_initial_timing_v1.py',T/'verification.json']}};(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
