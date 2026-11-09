"""SAT check on exact native collision-mask gate cone, with negative mutation."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_native_ram_gates_v3_2026-10-09/gates.json';m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})));D=E/'full_native_pending_hit_mask_v1_2026-10-09';D.mkdir(exist_ok=True)
yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys'
drivers={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};leaves=set();cone={};targets=[]
boundary=set()
for bank in range(4):
 for suffix in ['pa','ra','pw']:
  boundary.update(m['netnames'][f'dataCache_1.ways_0_data_symbol{bank}.s0.'+suffix]['bits'])
def visit(b):
 if isinstance(b,str):return
 if b in cone or b in leaves:return
 if b in boundary:leaves.add(b);return
 pair=drivers.get(b)
 if not pair or pair[1]['type'].startswith('$_DFF'):
  leaves.add(b);return
 n,c=pair;assert c['type'] in ['$_AND_','$_OR_','$_XOR_','$_NOT_']
 cone[b]=(n,c)
 for p,bs in c['connections'].items():
  if c['port_directions'][p]=='input':
   for x in bs:visit(x)
for bank in range(4):
 prefix=f'dataCache_1.ways_0_data_symbol{bank}.s0';q=m['netnames'][prefix+'.hit']['bits'][0];pw=m['netnames'][prefix+'.pw']['bits'][0];cell=drivers[q][1];hit=cell['connections']['D'][0];visit(hit);targets.append({'bank':bank,'hit_q':q,'hit_D':hit,'pw':pw,'cell':drivers[hit][0]})
def ref(b):return f'w{b}' if isinstance(b,int) else "1'b"+b
ops={'$_AND_':'&','$_OR_':'|','$_XOR_':'^'}
def emit(mutated=False):
 lines=['module check_hit('+','.join('input '+ref(b) for b in sorted(leaves))+',output bad);']
 for b in sorted(cone):lines.append('wire '+ref(b)+';')
 for b,(name,c) in sorted(cone.items()):
  co=c['connections'];t=c['type'];op=ops.get(t)
  if mutated and b==targets[0]['hit_D']:op='|'
  rhs=('~'+ref(co['A'][0])) if t=='$_NOT_' else f"{ref(co['A'][0])} {op} {ref(co['B'][0])}"
  lines.append(f'assign {ref(b)} = {rhs};')
 lines.append('assign bad = '+' | '.join(f'({ref(r["hit_D"])} & ~{ref(r["pw"])})' for r in targets)+';\nendmodule\n');return '\n'.join(lines)
results=[]
for mutated in [False,True]:
 name='negative_or' if mutated else 'actual';v=D/(name+'.v');v.write_text(emit(mutated));script=f'read_verilog {v}; hierarchy -top check_hit; proc; opt; check -assert; sat -prove bad 0 -show-inputs -show-outputs'
 run=subprocess.run([str(yosys),'-p',script],capture_output=True,text=True,timeout=60);log=run.stdout+run.stderr;(D/(name+'.log')).write_text(log)
 success='SAT proof finished - no model found: SUCCESS!' in log;fail='SAT proof finished - model found: FAIL!' in log
 assert run.returncode==0 and (fail if mutated else success)
 results.append({'variant':name,'exit_code':run.returncode,'success':success,'counterexample':fail})
out={'input_sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'yosys_sha256':hashlib.sha256(yosys.read_bytes()).hexdigest(),'targets':targets,'leaf_bits':sorted(leaves),'actual_cells':{str(b):{'name':n,'cell':c} for b,(n,c) in cone.items()},'results':results,'scope':'Two-state exact actual native gate cone: pw=0 implies hit next data=0 for arbitrary pending/read address states. Negative OR mutation must fail. No initial hit-state value, read-visible mux relation, macro scheduling, ABC/export or Full admission.'};(D/'mask_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'gate_count':len(cone),'leaf_count':len(leaves),'results':results},indent=2))
