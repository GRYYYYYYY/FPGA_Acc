"""Conservative combinational reachability from four observed unknown CSR lanes."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json';T=E/'full_functional_clear_startup_trace_v1_2026-10-09/startup_state_audit.json'
m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));obs=json.loads(T.read_text())['actual_12_lane_observations'];seeds=[3056,3059,3561,3562];assert all(obs[str(b)]['binary_postedge_cycles']==0 for b in seeds)
graph=collections.defaultdict(list);state_sinks=collections.defaultdict(list);memory_sinks=collections.defaultdict(list)
for name,c in m['cells'].items():
 ins=[b for p,bs in c['connections'].items() if c['port_directions'][p]=='input' for b in bs if isinstance(b,int)]
 if 'dff' in c['type'].lower():
  for b in ins:state_sinks[b].append(name)
  continue
 if c['type'].startswith('$mem'):
  for b in ins:memory_sinks[b].append(name)
  continue
 outs=[b for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)]
 for b in ins:
  for y in outs:graph[b].append((y,name))
outputs=collections.defaultdict(list)
for n,p in m['ports'].items():
 if p['direction']=='output':
  for i,b in enumerate(p['bits']):outputs[b].append({'port':n,'lane':i})
records=[]
for b in seeds:
 parent={b:None};todo=collections.deque([b])
 while todo:
  x=todo.popleft()
  for y,n in graph[x]:
   if y not in parent:parent[y]=(x,n);todo.append(y)
 paths=[]
 for y in sorted(set(parent)&set(outputs)):
  chain=[];cur=y
  while parent[cur] is not None:
   prev,n=parent[cur];chain.append({'input_bit':prev,'cell':n,'type':m['cells'][n]['type'],'output_bit':cur});cur=prev
  paths.append({'bit':y,'ports':outputs[y],'path':list(reversed(chain))})
 records.append({'source_bit':b,'reachable_combinational_bits':len(parent),'output_paths':paths,'reachable_register_input_cells':sorted({n for x in parent for n in state_sinks[x]}),'reachable_memory_input_cells':sorted({n for x in parent for n in memory_sinks[x]})})
for r in records:
 r['register_sink_aliases']={n:[name for name,net in m['netnames'].items() if not name.startswith('$') and set(m['cells'][n]['connections']['Q']).intersection(net['bits'])] for n in r['reachable_register_input_cells']}
out={'records':records,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,T]},'scope':'Whole-cell conservative combinational dependency, stopping at FF and memory cells. Paths establish structural possibility only, not semantic sensitization or actual replay mismatch causality. No path would establish combinational noninterference only, not sequential or memory noninterference.'}
d=E/'full_unknown_csr_combinational_influence_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'influence_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{'bit':r['source_bit'],'output_ports':sorted({p['port'] for path in r['output_paths'] for p in path['ports']}),'register_input_cells':len(r['reachable_register_input_cells']),'memory_input_cells':len(r['reachable_memory_input_cells'])} for r in records],indent=2))
