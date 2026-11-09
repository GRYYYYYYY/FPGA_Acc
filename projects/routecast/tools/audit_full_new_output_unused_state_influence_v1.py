"""Conservative source noninterference for four new output-closure aliases."""
import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json';P=E/'full_external_output_state_closure_v1_2026-10-09'
m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})));extension=json.loads((P/'extension_mapping_audit.json').read_text());seeds=[r['source_bit'] for r in extension['rows'] if r['mapped_driver'] is None and r['source_bit'] not in json.loads((P/'closure_audit.json').read_text())['input_boundary_bits']];assert len(seeds)==4
targets={r['source_bit'] for r in json.loads((P/'mapping_candidates.json').read_text())['records']} - set(seeds);outbits={b for p in m['ports'].values() if p['direction']=='output' for b in p['bits']}
graph=collections.defaultdict(set);rules=collections.Counter();meminputs=set()
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
 records.append({'source_bit':b,'reachable_bits':sorted(reached),'external_outputs':sorted(reached&outbits),'other_boundary_states':sorted(reached&targets),'memory_write_inputs':sorted(reached&meminputs)})
out={'records':records,'rules':dict(rules),'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,P/'mapping_candidates.json',P/'extension_mapping_audit.json']},'scope':'Per-bit conservative mux/arithmetic/register influence with all memory-write inputs as sinks. Noninterference of four extra undriven-mapped source bits, not initial/native/global equivalence.'}
D=E/'full_new_output_unused_state_influence_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'influence_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{'bit':r['source_bit'],'outputs':len(r['external_outputs']),'other_states':len(r['other_boundary_states']),'memory_writes':len(r['memory_write_inputs'])} for r in records]));assert all(not r['external_outputs'] and not r['other_boundary_states'] and not r['memory_write_inputs'] for r in records)
