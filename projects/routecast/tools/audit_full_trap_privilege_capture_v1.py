"""Inventory actual trap privilege state; do not infer initialized equality."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
paths=[R/'experiments/full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json',R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json',R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v']
mods=[max(json.loads(p.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{}))) for p in paths[:2]]
s,n=mods;q=s['netnames']['CsrPlugin_interrupt_targetPrivilege']['bits']
regs=[{'name':k,**c} for k,c in s['cells'].items() if c['connections'].get('Q')==q]
assert len(regs)==1 and regs[0]['type']=='$dff'
assert n['netnames']['CsrPlugin_interrupt_targetPrivilege']['bits']==['1','1']
assert n['netnames']['CsrPlugin_targetPrivilege']['bits']==['1','1']
assert n['netnames']['when_CsrPlugin_l1318']['bits']==['1']
text=paths[2].read_text();assert "assign CsrPlugin_trapEnterDebug = 1'b0;" in text
assert text.count("CsrPlugin_interrupt_targetPrivilege <= 2'b11;")==3
assert 'CsrPlugin_mepc <= writeBack_PC;' in text
aliases={k:v for k,v in s['netnames'].items() if any(b in q for b in v['bits'])}
assert not any('init' in v.get('attributes',{}) for v in aliases.values())
# Preserve complete actual combinational D cone and boundary, rather than only names.
drivers={b:(k,c) for k,c in s['cells'].items() for port,bits in c['connections'].items() if c['port_directions'][port]=='output' for b in bits if isinstance(b,int)}
cone={};boundary=set()
def visit(b):
 if not isinstance(b,int):return
 if b not in drivers:boundary.add(b);return
 k,c=drivers[b]
 if 'ff' in c['type'].lower() or 'mem' in c['type'].lower():boundary.add(b);return
 if k in cone:return
 cone[k]=c
 for port,bits in c['connections'].items():
  if c['port_directions'][port]=='input':
   for x in bits:visit(x)
for b in regs[0]['connections']['D']:visit(b)
out={'source_register':regs[0],'source_aliases':aliases,'capture_cone':cone,'boundary_bits':sorted(boundary),'native_target_privilege':['1','1'],'debug_guard':'Original explicit trapEnterDebug=0; native when_l1318=1.','conclusion':'Source interrupt target privilege has no reset/init and three literal11 writes. Native folds it to11. Initial equality is not established. Trap mepc consumes full writeBack_PC.','next_obligation':'Prove capture history under actual interruptJump/interrupt_valid, including reset and four-state scope; exception target privilege is a separate constant path.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
d=R/'experiments/full_trap_privilege_capture_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'capture_cells':len(cone),'boundary_bits':len(boundary),'conclusion':out['conclusion']}))
