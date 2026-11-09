"""Check actual source-proc mcause read muxes and known-select masking."""
import hashlib,itertools,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=R/'experiments/full_original_source_proc_state_v1_2026-10-09/source_proc.json';V=R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v'
m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));nets=m['netnames'];bits=nets['_zz_CsrPlugin_csrMapping_readDataInit_6']['bits'];select=nets['execute_CsrPlugin_csr_834']['bits'];drivers={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};cells={drivers[b][0]:drivers[b][1] for b in bits if isinstance(b,int)}
assert len(cells)==2
for c in cells.values():assert c['type']=='$mux' and c['connections']['S']==select and set(c['connections']['A'])=={'0'}
assert cells[drivers[bits[0]][0]]['connections']['B']==nets['CsrPlugin_mcause_exceptionCode']['bits']
assert cells[drivers[bits[31]][0]]['connections']['B']==nets['CsrPlugin_mcause_interrupt']['bits']
assert all(b=='0' for b in bits[4:31])
cases=0;negative=0
for values in itertools.product('01x',repeat=5):
 for s in ['0','1']:
  inputs=dict(zip(nets['CsrPlugin_mcause_exceptionCode']['bits']+nets['CsrPlugin_mcause_interrupt']['bits'],values));out={}
  for c in cells.values():
   co=c['connections']
   for a,b,y in zip(co['A'],co['B'],co['Y']):out[y]=a if s=='0' else inputs[b]
  result=[out.get(b,b) for b in bits]
  if s=='0':assert set(result)=={'0'}
  else:
   assert result[:4]==list(values[:4]) and result[31]==values[4]
   negative+=any(v!='0' for v in values)
  cases+=1
out={'actual_cells':cells,'select_bit':select[0],'checked_cases':cases,'selected_nonzero_or_unknown_negative_cases':negative,'source_lines':V.read_text().splitlines()[5537:5544],'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,V]},'scope':'Exact two source-proc muxes with known binary select and arbitrary 0/1/X stored cause/interrupt bits. Select0 masks complete mcause contribution; select1 exposes it. Does not prove select0 in actual replay, unknown-select procedural equivalence, total CSR value, register capture, global relation or Full admission.'}
d=R/'experiments/full_actual_mcause_read_mask_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'mask_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['actual_cells','source_lines','hashes']},indent=2))
