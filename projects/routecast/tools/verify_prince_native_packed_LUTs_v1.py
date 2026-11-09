"""Compare native loaded masks/nets with independently resolved BLIF/XML reference."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 o=R/'experiments/prince_native_packed_LUTs_v1_2026-10-20';ref=R/'experiments/prince_LUT_reference_v1_2026-10-20';bindings={}
 for p in [o/'protocol.json',ref/'verification.json']:
  d=json.loads(p.read_text())
  for name,h in d['bindings'].items():assert sha(name)==h;bindings[name]=h
 receipt=json.loads((o/'receipt.json').read_text());assert receipt['exit_code']==0
 export=o/'loaded_LUTs.tsv';assert sha(export)==receipt['export_sha256']
 refs={r['atom']:r for r in map(json.loads,(ref/'derived_physical_LUTs.jsonl').open())};seen=set();rows=0;slice_rows=0;outside_difference=0;opens=0
 for line in export.open():
  name,width,signals,mask=line.rstrip('\n').split('\t');width=int(width);signals=signals.split(',');assert name in refs and name not in seen;seen.add(name)
  r=refs[name];rot=r['physical_to_logical'];assert width==len(rot)==len(signals) and len(mask)==1<<width and set(mask)<=set('01')
  for i,j in enumerate(rot):assert signals[i]==('open' if j=='open' else r['logical_inputs'][int(j)])
  for assignment,bit in enumerate(mask):
   zero_open=all(not((assignment>>i)&1) for i,j in enumerate(rot) if j=='open')
   if zero_open:assert bit==r['derived_physical_truth'][assignment];slice_rows+=1
   elif bit!=r['derived_physical_truth'][assignment]:outside_difference+=1
  rows+=len(mask);opens+=signals.count('open')
 assert seen==set(refs) and len(seen)==2096
 for p in [o/'protocol.json',o/'receipt.json',export,ref/'verification.json',ref/'derived_physical_LUTs.jsonl',Path(__file__)]:bindings[str(p)]=sha(p)
 for p,h in bindings.items():assert sha(p)==h
 result=dict(status='native_loaded_masks_and_physical_nets_verified_on_zero_open_input_slice',LUT_atoms=len(seen),physical_mask_rows=rows,zero_open_input_rows_verified=slice_rows,open_input_pins=opens,outside_zero_slice_reference_differences=outside_difference,bindings=bindings,scope='Native packing state versus independently resolved BLIF/XML. Full mask differences outside the zero-open slice counted explicitly. Default unconnected inputs can be X; no whole-circuit four-state, timing, unseen or routing evidence.',strict_unseen_admitted=False,new_route_labels=False)
 with (o/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print({k:v for k,v in result.items() if k not in ['bindings','scope']})
if __name__=='__main__':main()
