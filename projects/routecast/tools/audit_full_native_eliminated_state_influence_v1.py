"""Conservative intermediate influence audit for undriven native aliases."""
import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
F=E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json'
M=E/'full_structural_native_register_mapping_v1_2026-10-09/mapping_audit.json'
m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})))
a=json.loads(M.read_text())
seeds=[r['bit'] for r in a['rows'] if r['status']=='unresolved']
targets={r['bit'] for r in a['rows'] if r['status']=='unique_native_state'}
outbits={b for v in m['ports'].values() if v['direction']=='output' for b in v['bits']}
graph=collections.defaultdict(set);rules=collections.Counter();meminputs=set()
def scalar(bs,i):
 return bs[i:i+1]
for n,c in m['cells'].items():
 t=c['type'];co=c['connections'];ins={p:bs for p,bs in co.items() if c['port_directions'][p]=='input'};allins=[b for bs in ins.values() for b in bs]
 if t.startswith('$memwr') or t=='dual_port_ram':meminputs.update(b for b in allins if isinstance(b,int))
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
 records.append({'structural_bit':b,'reachable_bits':sorted(reached),'external_outputs':sorted(reached&outbits),'retained_states':sorted(reached&targets),'memory_inputs':sorted(reached&meminputs)})
counts={k:sum(bool(r[k]) for r in records) for k in ['external_outputs','retained_states','memory_inputs']}
D=E/'full_native_eliminated_state_influence_v1_2026-10-09';D.mkdir(exist_ok=True)
out={'records':records,'counts':counts,'rules':dict(rules),'bindings':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [F,M]},'scope':'Conservative intermediate connectivity influence. All macro inputs are sinks; reaching one does not by itself prove observable influence. No reset/init, transition equivalence, or Full admission claim.'}
(D/'influence_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'seed_count':len(seeds),'counts':counts},indent=2))
