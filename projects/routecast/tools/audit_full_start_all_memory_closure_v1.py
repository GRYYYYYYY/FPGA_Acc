"""Conservative actual-cell dependency closure, never an equivalence proof."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
files=[E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json',E/'full_start_tags_dependency_closure_v1_2026-10-09/audit.json',E/'full_all_memory_control_sat_v1_2026-10-09/protocol.json']
a,c,t=[json.loads(f.read_text()) for f in files];m=next(iter(a['modules'].values()))
stop=lambda v: bool(re.match(r'^\$(?:[as]?dff|dlatch|mem)',v['type']))
drv={b:(n,v) for n,v in m['cells'].items() for p,bs in v['connections'].items() if v['port_directions'][p]=='output' for b in bs if isinstance(b,int)}
inputs={b for p,v in m['ports'].items() if v['direction']=='input' for b in v['bits']}
def cone(roots):
 todo=list(roots);seen=set();boundary=set();used=set()
 while todo:
  b=todo.pop()
  if not isinstance(b,int) or b in seen:continue
  seen.add(b)
  if b not in drv or stop(drv[b][1]):boundary.add(b);continue
  n,v=drv[b]
  if n in used:continue
  used.add(n);todo.extend(b for p,bs in v['connections'].items() if v['port_directions'][p]=='input' for b in bs)
 return boundary,used
initial=set(c['closure_bits'])|set(t['source_boundary']);pending=set(initial);allbits=set(initial);records={};rounds=[]
while pending:
 new=set()
 for b in sorted(pending):
  if b not in drv:continue
  n,v=drv[b]
  if n in records:continue
  if not stop(v):raise AssertionError((b,n,v['type']))
  roots=[b for p,bs in v['connections'].items() if v['port_directions'][p]=='input' for b in bs]
  deps,comb=cone(roots);records[n]={'type':v['type'],'state_outputs':{p:bs for p,bs in v['connections'].items() if v['port_directions'][p]=='output'},'dependency_bits':sorted(deps),'comb_cell_count':len(comb),'parameters':v['parameters']};new.update(deps-allbits)
 rounds.append({'frontier_bits':len(pending),'added_bits':len(new),'state_cells_total':len(records)});allbits.update(new);pending=new
counts={}
for b in allbits:
 kind=drv[b][1]['type'] if b in drv else ('top_input' if b in inputs else 'undriven');counts[kind]=counts.get(kind,0)+1
D=E/'full_start_all_memory_dependency_closure_v1_2026-10-09';D.mkdir(exist_ok=False)
out={'bindings':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),*files]},'seed_bits':sorted(initial),'closure_bits':sorted(allbits),'rounds':rounds,'boundary_type_counts':counts,'state_cells':records,'scope':'Conservative whole-cell source dependency fixed point from prior closure and all memory control cuts. Source dependency closure is not source/native relational closure; memory arrays, reset/initial correspondence, state transfer and product admission remain obligations.','relational_closure_proved':False,'functional_admission':False};(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'seed_bits':len(initial),'closure_bits':len(allbits),'rounds':rounds,'types':counts}))
