"""Per-bit four-state frames and exhaustive end-memory comparison."""
import json,hashlib,itertools,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'mcml_order_memory_binary_v4_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(path,prefix):
 with path.open() as f:
  for line in f:
   if line.startswith(prefix):yield line.strip().split(',')[1:]
def main():
 protocol=json.loads((D/'protocol.json').read_text())
 for p,h in protocol['bindings'].items():assert sha(Path(p))==h,p
 stages=json.loads((D/'results.json').read_text())['rows'];assert len(stages)==6 and all(r['exit_code']==0 for r in stages);assert protocol['frame_radix']=='binary'
 library=next(Path(p) for p in protocol['bindings'] if p.endswith('/vtr_flow/primitives.v'));text=library.read_text();start=text.index('module dual_port_ram');a=text.index('    always@(posedge clk)',start);b=text.index('    always@(posedge clk)',a+1);end=text.index('endmodule',b);assert (D/'swapped_primitives.v').read_text()==text[:a]+text[b:end]+text[a:b]+text[end:]
 tb=(D/'tb.v').read_text();assert 'force ' not in tb and '$deposit' not in tb;assert 'integer cycle,row;' in tb;assert tb.count('dut.')>=17
 for arm in ['original','swapped']:
  cmd=[s['command'] for s in stages if s['arm']==arm];assert len(cmd)==3 and str(D/'tb.v') in cmd[0]
 fields=protocol['fields'];spec={g['instance']:g for g in protocol['memory_groups']};widths={f:protocol['output_widths'][f[4:]] if f.startswith('top:') else spec[f[4:]+'.dpram1']['width'] for f in fields};counts={f:{'differing_cycles':0,'both_defined_differing_cycles':0,'first_difference':None} for f in fields};states=set();last_state=None
 for cycle,pair in enumerate(itertools.zip_longest(lines(D/'original/xsim.log','FRAME,'),lines(D/'swapped/xsim.log','FRAME,'))):
  aa,bb=pair;assert aa is not None and bb is not None;assert len(aa)==len(bb)==len(fields)+2;assert int(aa[0])==int(bb[0])==cycle;expected=str(int(any(a<=cycle<b for a,b in protocol['read_constants_intervals_half_open'])));assert aa[1]==bb[1]==expected
  for f,x,y in zip(fields,aa[2:],bb[2:]):
   x,y=x.lower(),y.lower();assert len(x)==len(y)==widths[f] and set(x+y)<={'0','1','x','z'}
   if f=='top:r_state':
    if set(x)<={'0','1'}:last_state=int(x,2);states.add(last_state)
   if x!=y:
    r=counts[f];r['differing_cycles']+=1;r['both_defined_differing_cycles']+=set(x+y)<={'0','1'}
    if r['first_difference'] is None:r['first_difference']={'cycle':cycle,'original':x,'swapped':y}
 assert cycle+1==90000
 memory={n:{'rows':g['rows'],'width':g['width'],'differing_words':0,'both_defined_differing_words':0,'unknown_words_original':0,'unknown_words_swapped':0,'first_difference':None} for n,g in spec.items()};expected=((g['instance'],i) for g in protocol['memory_groups'] for i in range(g['rows']));total=0
 for index,triple in enumerate(itertools.zip_longest(expected,lines(D/'original/xsim.log','MEMORY_END,'),lines(D/'swapped/xsim.log','MEMORY_END,'))):
  key,aa,bb=triple;assert key is not None and aa is not None and bb is not None;name,addr=key;assert aa[0]==bb[0]==name and int(aa[1])==int(bb[1])==addr;x,y=aa[2].lower(),bb[2].lower();r=memory[name];assert len(x)==len(y)==r['width'] and set(x+y)<={'0','1','x','z'};r['unknown_words_original']+=not(set(x)<={'0','1'});r['unknown_words_swapped']+=not(set(y)<={'0','1'})
  if x!=y:
   r['differing_words']+=1;r['both_defined_differing_words']+=set(x+y)<={'0','1'}
   if r['first_difference'] is None:r['first_difference']={'address':addr,'original':x,'swapped':y}
  total+=1
 assert total==sum(g['rows'] for g in protocol['memory_groups'])==232448
 for arm in ['original','swapped']:
  assert 'MATCHED_MEMORY_REPLAY_COMPLETE cycles=90000' in (D/arm/'xsim.log').read_text()
 out={'status':'BINARY_PER_BIT_MCML_FRAMES_AND_ALL_END_MEMORY_WORDS_VERIFIED','cycles':90000,'top_outputs':{f:r for f,r in counts.items() if f.startswith('top:')},'RAM_read_outputs':{f:r for f,r in counts.items() if f.startswith('ram:')},'end_memory_groups':memory,'end_memory_words_compared':total,'states_reached_original':sorted(states),'last_state_original':last_state,'top_sample_differences':sum(r['differing_cycles'] for f,r in counts.items() if f.startswith('top:')),'end_memory_differences':sum(r['differing_words'] for r in memory.values()),'bindings':{str(p.relative_to(R)):sha(p) for p in [D/'tb.v',D/'results.json',D/'original/xsim.log',D/'swapped/xsim.log']},'scope':'Bit-exact four-state sampled outputs and all memory words at one end snapshot for frozen finite input sequence. Earlier hexadecimal equality is representation-level only where unknown nibbles can hide known bits. No universal/state-inductive equivalence, completed computation/readout, canonical collision mode or actual mapped-source admission.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status']);print('top differences',out['top_sample_differences'],'memory differences',out['end_memory_differences'],'last state',last_state)
if __name__=='__main__':main()
