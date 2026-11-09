"""Concrete three-valued netlist trace; not an HDL simulator or equivalence proof."""
import json, hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'experiments/standard_parmys_ram_mapping_v2_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def land(a,b):return 0 if a==0 or b==0 else (1 if a==b==1 else None)
def lor(xs):return 1 if 1 in xs else (None if None in xs else 0)
def simulate(name):
 p=D/name/'mapped.json';m=json.loads(p.read_text())['modules']['probe'];cells=list(m['cells'].values());rams=[c for c in cells if c['type']=='dual_port_ram'];gates=[c for c in cells if c['type']!='dual_port_ram'];assert {c['type'] for c in gates}<={'$and','$reduce_or','$reduce_and','$logic_not'}
 ports=m['ports'];inputs={};states=[{'mem':{},'out1':None,'out2':None} for c in rams]
 def put(k,val):
  if k in ports:
   for i,b in enumerate(ports[k]['bits']):inputs[b]=(val>>i)&1
  else:
   for i in range(64):
    if f'{k}~{i}' in ports:inputs[ports[f'{k}~{i}']['bits'][0]]=(val>>i)&1
 def evaluate():
  v=dict(inputs);v.update({'0':0,'1':1,'x':None,'z':None})
  for c,s in zip(rams,states):
   for k in ['out1','out2']:v[c['connections'][k][0]]=s[k]
  pending=gates[:]
  while pending:
   nxt=[]
   for c in pending:
    z=c['connections'];ins=z['A']+z.get('B',[])
    if any(b not in v for b in ins):nxt.append(c);continue
    a=[v[b] for b in z['A']];t=c['type']
    if t=='$and':y=[land(x,v[b]) for x,b in zip(a,z['B'])]
    elif t=='$reduce_or':y=[lor(a)]
    elif t=='$reduce_and':y=[0 if 0 in a else (None if None in a else 1)]
    else:y=[None if lor(a) is None else 1-lor(a)]
    assert len(y)==len(z['Y']);v.update(zip(z['Y'],y))
   assert len(nxt)<len(pending),'unresolved netlist';pending=nxt
  return v
 def number(v,bits):
  xs=[v[b] for b in bits];return None if None in xs else sum(x<<i for i,x in enumerate(xs))
 def output(v):
  if 'out1' in ports:return number(v,ports['out1']['bits'])
  return number(v,[ports[f'out1~{i}']['bits'][0] for i in range(32 if name=='dp13x32' else 36)])
 def tick():
  v=evaluate()
  for c,s in zip(rams,states):
   z=c['connections'];a=number(v,z['addr1']);a2=number(v,z['addr2']);we=number(v,z['we1']);assert number(v,z['we2'])==0
   if we==1:s['mem'][a]=number(v,z['data1'])
   s['out1']=s['mem'].get(a);s['out2']=s['mem'].get(a2)
  return evaluate()
 width=32 if name=='dp13x32' else 36
 for k in ['clk','we1','addr1','addr2','data1']:put(k,0)
 trace=[];reference_mem={};reference_out=None
 for addr,data,we in [(0,1,1),(1,0,1),(0,0,0)]:
  put('addr1',addr);put('addr2',17);put('data1',data);put('we1',we)
  if we:reference_mem[addr]=data
  reference_out=reference_mem.get(addr);actual=output(tick());assert actual==reference_out,(name,actual,reference_out)
  trace.append(dict(event='posedge',address=addr,we=we,data=data,reference_out1=reference_out,mapped_out1=actual))
 put('addr1',1);actual=output(evaluate());assert reference_out==1 and actual==0,(name,reference_out,actual,trace)
 trace.append(dict(event='address_change_without_clock_edge',address=1,reference_out1=reference_out,mapped_out1=actual))
 return dict(case=name,mapped_sha256=sha(p),ram_cells=len(rams),trace=trace,read_hold_counterexample=True,scope='Concrete defined out1 trace under original functional RAM model; no initial memory assumptions. Python three-valued evaluator, not HDL simulator/full equivalence proof. Port2 ignored; no port2 writes. Conditional on hard RAM implementing original synchronous primitive contract.')
def main():
 result=dict(status='BANKED_OUTPUT_HOLD_COUNTEREXAMPLE_UNDER_FUNCTIONAL_PRIMITIVE_CONTRACT',producer_sha256=sha(Path(__file__)),rows=[simulate(n) for n in ['dp13x32','dp16x36']],native_admitted=False,strict_unseen_admitted=False)
 (D/'banked_read_hold_audit_v1.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
