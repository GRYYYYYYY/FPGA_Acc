"""Conservative per-bit structural influence including register propagation."""
import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_start_tags_dependency_closure_v1_2026-10-09';F=E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json';m=next(iter(json.load(open(F))['modules'].values()));ob=json.load(open(P/'state_obligations.json'));seeds=[r['source_bit'] for r in ob['records'] if r['kind']=='undriven_candidate'];targets={r['source_bit'] for r in ob['records'] if r['kind'] in ['register_transfer','ram_visible_relation','constant_invariant']};outbits={b for v in m['ports'].values() if v['direction']=='output' for b in v['bits']};graph=collections.defaultdict(set);rules=collections.Counter();meminputs=set()
def scalar(bs,i):
 return bs[i:i+1]
for n,c in m['cells'].items():
 t=c['type'];co=c['connections'];ins={p:bs for p,bs in co.items() if c['port_directions'][p]=='input'};allins=[b for bs in ins.values() for b in bs]
 if t.startswith('$memwr'):meminputs.update(b for b in allins if isinstance(b,int))
 for port,bs in co.items():
  if c['port_directions'][port]!='output':continue
  for i,y in enumerate(bs):
   if not isinstance(y,int):continue
   rule='all_inputs_conservative';deps=allins
   if t=='$mux':deps=scalar(co['A'],i)+scalar(co['B'],i)+co['S'];rule='mux_lane'
   elif t=='$pmux':w=len(co['Y']);deps=scalar(co['A'],i)+co['B'][i::w]+co['S'];rule='pmux_lane'
   elif t in ['$add','$sub','$mul']:deps=co['A'][:i+1]+co['B'][:i+1];rule='low_modular_arithmetic'
   elif t in ['$and','$or','$xor','$not']:
    deps=[]
    for p in ['A','B']:
     if p not in co:continue
     vv=co[p];deps+=scalar(vv,i) if i<len(vv) else vv[-1:] if int(c['parameters'].get(p+'_SIGNED','0'),2) else []
    rule='bitwise_with_signed_extension'
   elif port=='Q' and t in ['$dff','$dffe','$adff','$adffe','$sdff','$sdffe','$sdffce']:
    deps=scalar(co['D'],i)+[b for p in ['EN','ARST','SRST'] for b in co.get(p,[])];rule='register_lane_with_controls'
   for b in deps:
    if isinstance(b,int):graph[b].add(y)
   rules[rule]+=1
records=[]
for b in seeds:
 reached={b};todo=[b]
 while todo:
  x=todo.pop()
  for y in graph.get(x,[]):
   if y not in reached:reached.add(y);todo.append(y)
 records.append({'source_bit':b,'reachable_bits':sorted(reached),'reachable_external_outputs':sorted(reached&outbits),'reachable_required_states':sorted(reached&targets),'reachable_memory_write_inputs':sorted(reached&meminputs)})
D=E/'full_unused_state_bit_influence_v1_2026-10-09';D.mkdir(exist_ok=False);out={'records':records,'rules':dict(rules),'bindings':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),F,P/'state_obligations.json']},'scope':'Conservative source bit influence for exact mux/pmux/arithmetic/register rules; unsupported cells all-input overapproximation. Memory write inputs are explicit observability sinks because array-content propagation is not represented by combinational graph. No initial or Full equivalence claim.','functional_admission':False};(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{'bit':r['source_bit'],'outputs':len(r['reachable_external_outputs']),'states':len(r['reachable_required_states']),'memory_write_inputs':len(r['reachable_memory_write_inputs']),'reach':len(r['reachable_bits'])} for r in records]))
