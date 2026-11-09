"""Conservative ternary evaluation of exact original/native debug-idle cuts."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_debug_idle_unknown_cone_v1_2026-10-09';D.mkdir(exist_ok=True)
def inv(x):return {'0':'1','1':'0','x':'x'}[x]
def AND(a,b):return '0' if '0' in [a,b] else ('1' if a==b=='1' else 'x')
def OR(a,b):return '1' if '1' in [a,b] else ('0' if a==b=='0' else 'x')
def mux(a,b,s):return a if s=='0' else (b if s=='1' else [x if x==y else 'x' for x,y in zip(a,b)])
results={};hashes={}
for label,rel in [('s','full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'),('n','full_native_ram_gates_v3_2026-10-09/gates.json')]:
 f=R/'experiments'/rel;original=max(json.loads(f.read_text())['modules'].values(),key=lambda m:len(m['cells']));q=original['netnames']['switch_Fetcher_l365']['bits'];valid=original['ports']['debug_bus_cmd_valid']['bits'][0];cut=R/'experiments/full_debug_injection_idle_v1_2026-10-09'/(label+'_cut.json');m=json.loads(cut.read_text())['modules']['actual_cut'];trials=[]
 for other in ['x','0','1']:
  vals={b:other for b in m['ports']['boundary']['bits']};vals.update({b:'0' for b in q+[valid]});pending=dict(m['cells'])
  def get(bs):return [vals[b] if isinstance(b,int) else b for b in bs]
  while pending:
   progress=False
   for name,c in list(pending.items()):
    if any(isinstance(b,int) and b not in vals for p,bs in c['connections'].items() if c['port_directions'][p]=='input' for b in bs):continue
    t=c['type'];ps={p:get(bs) for p,bs in c['connections'].items() if c['port_directions'][p]=='input'};A=ps.get('A',[]);B=ps.get('B',[]);Y=c['connections']['Y'];width=len(Y)
    if t in ['$not','$_NOT_']:o=[inv(x) for x in A]
    elif t in ['$and','$_AND_','$logic_and']:o=[AND(a,b) for a,b in zip(A,B)] if t!='$logic_and' else [AND('1' if '1' in A else ('0' if set(A)=={'0'} else 'x'),'1' if '1' in B else ('0' if set(B)=={'0'} else 'x'))]
    elif t in ['$logic_or','$logic_not','$reduce_or']:
     red=lambda a:'1' if '1' in a else ('0' if set(a)=={'0'} else 'x')
     o=[OR(red(A),red(B))] if t=='$logic_or' else ([inv(red(A))] if t=='$logic_not' else [red(A)])
    elif t=='$_OR_':o=[OR(a,b) for a,b in zip(A,B)]
    elif t=='$_XOR_':o=['x' if 'x' in [a,b] else str(int(a)^int(b)) for a,b in zip(A,B)]
    elif t in ['$eq','$ne']:
     size=max(len(A),len(B));signed=all(int(c['parameters'].get(k,'0'),2) for k in ['A_SIGNED','B_SIGNED']);A=A+([A[-1] if signed else '0']*(size-len(A)));B=B+([B[-1] if signed else '0']*(size-len(B)))
     equal='0' if any(a!=b and 'x' not in [a,b] for a,b in zip(A,B)) else ('x' if 'x' in A+B else '1');o=[inv(equal) if t=='$ne' else equal]
    elif t in ['$mux','$_MUX_']:o=mux(A,B,ps['S'][0])
    elif t=='$pmux':
     selectors=ps['S'];active=[i for i,s in enumerate(selectors) if s!='0']
     if not active:o=A
     elif len(active)==1:o=mux(A,B[active[0]*width:(active[0]+1)*width],selectors[active[0]])
     else:o=['x']*width
    else:raise AssertionError(t)
    assert len(o)==width,(t,len(o),width)
    vals.update(zip(Y,o));del pending[name];progress=True
   assert progress,'dependency cycle'
  roots=get(m['ports']['roots']['bits']);trials.append({'other_boundary_value':other,'roots':roots,'all_roots_zero':set(roots)=={'0'}})
 results[label]=trials
 hashes[str(cut.relative_to(R))]=hashlib.sha256(cut.read_bytes()).hexdigest();hashes[str(f.relative_to(R))]=hashlib.sha256(f.read_bytes()).hexdigest()
out={'results':results,'scope':'Exact proc/native cuts with idleQ000/commandvalid0; other binary-state boundaries independently unknown in X trial, using conservative gate ternary evaluation. Not original procedural event simulator or actual exported LUT cone/event validation.','hashes':hashes};(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(results,indent=2))
