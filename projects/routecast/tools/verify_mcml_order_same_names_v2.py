"""Streaming paired-frame verifier; no assumption that finite agreement is equivalence."""
import json,hashlib,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/mcml_collision_order_same_names_v2_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 protocol=json.loads((D/'protocol.json').read_text())
 for p,h in protocol['bindings'].items():assert sha(Path(p))==h,p
 source=next(Path(p) for p in protocol['bindings'] if p.endswith('/benchmarks/verilog/mcml.v'));library=next(Path(p) for p in protocol['bindings'] if p.endswith('/vtr_flow/primitives.v'));original=library.read_text();start=original.index('module dual_port_ram');a=original.index('    always@(posedge clk)',start);b=original.index('    always@(posedge clk)',a+1);end=original.index('endmodule',b);assert (D/'swapped_primitives.v').read_text()==original[:a]+original[b:end]+original[a:b]+original[end:]
 rows=json.loads((D/'results.json').read_text())['rows'];assert len(rows)==6 and all(r['exit_code']==0 for r in rows)
 for arm in ['original','swapped']:
  commands=[r['command'] for r in rows if r['arm']==arm];assert len(commands)==3;assert str(source) in commands[0] and str(D/'tb.v') in commands[0];assert commands[1][1:]==['tb','-s','matched_order']
 fields=protocol['fields'];counts={n:{'differing_cycles':0,'both_values_binary_differing_cycles':0,'first_difference':None} for n in fields};states=set();inputs=protocol['read_constants_intervals_half_open']
 def frames(path):
  complete=False
  with path.open() as f:
   for line in f:
    if line.startswith('FRAME,'):yield line.strip().split(',')[1:]
    if 'MATCHED_ORDER_REPLAY_COMPLETE cycles=90000' in line:complete=True
  assert complete
 count=0
 for idx,pair in enumerate(itertools.zip_longest(frames(D/'original/xsim.log'),frames(D/'swapped/xsim.log'))):
  aa,bb=pair;assert aa is not None and bb is not None;assert len(aa)==len(bb)==len(fields)+2;assert int(aa[0])==int(bb[0])==idx;expected=str(int(any(a<=idx<b for a,b in inputs)));assert aa[1]==bb[1]==expected
  for n,x,y in zip(fields,aa[2:],bb[2:]):
   x,y=x.lower(),y.lower()
   if n=='top:r_state' and all(c not in x for c in 'xz'):states.add(int(x,16))
   if x!=y:
    r=counts[n];r['differing_cycles']+=1;r['both_values_binary_differing_cycles']+=all(c not in x+y for c in 'xz')
    if r['first_difference'] is None:r['first_difference']={'cycle':idx,'original':x,'swapped':y}
  count+=1
 assert count==90000
 top={k:v for k,v in counts.items() if k.startswith('top:')};ram={k:v for k,v in counts.items() if k.startswith('ram:')};out={'status':'SAME_NAME_SAME_STIMULUS_ORDER_REPLAY_FRAMES_VERIFIED','cycles':count,'top_output_fields':top,'RAM_output_fields':ram,'states_reached_original':sorted(states),'any_top_output_difference':any(r['differing_cycles'] for r in top.values()),'all_RAM_fields_have_difference':all(r['differing_cycles'] for r in ram.values()),'bindings':{str(p.relative_to(R)):sha(p) for p in [D/'tb.v',D/'results.json',D/'original/xsim.log',D/'swapped/xsim.log']},'scope':'Finite concrete four-state event simulations with identical top names/inputs and only library process-order intervention. Equality on sampled top outputs is not universal observational equivalence, intended ROM/application correctness, physical RAM read mode or mapped-source admission.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status']);print('top_difference',out['any_top_output_difference'],'RAM_all_differ',out['all_RAM_fields_have_difference'],'states',out['states_reached_original'])
if __name__=='__main__':main()
