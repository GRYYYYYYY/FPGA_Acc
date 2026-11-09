"""Conservative source state closure for ALL external outputs and RAM writes."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json';P=E/'full_start_all_memory_dependency_closure_v1_2026-10-09/mapping_candidates.json';m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})));old={r['source_bit'] for r in json.loads(P.read_text())['records']};drivers={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)};inputs={b for p in m['ports'].values() if p['direction']=='input' for b in p['bits']};outputs={b for p in m['ports'].values() if p['direction']=='output' for b in p['bits']};roots=set(outputs);writes=[]
for n,c in m['cells'].items():
 if c['type'].startswith('$memwr'):
  writes.append(n);roots.update(b for p,bs in c['connections'].items() if c['port_directions'][p]=='input' for b in bs)
todo=list(roots);visited=set();cells={};boundary=set();missing=set();state_records=[]
while todo:
 bit=todo.pop()
 if not isinstance(bit,int) or bit in visited:continue
 visited.add(bit)
 if bit in inputs:boundary.add(bit);continue
 if bit not in drivers:missing.add(bit);continue
 name,c=drivers[bit]
 if name in cells:continue
 cells[name]=c
 if 'dff' in c['type'].lower() or c['type'].startswith('$memrd'):
  statebits=[b for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)];boundary.update(statebits);state_records.append({'cell':name,'type':c['type'],'state_bits':statebits})
 todo.extend(b for p,bs in c['connections'].items() if c['port_directions'][p]=='input' for b in bs)
extra=sorted(boundary-old)
out={'external_output_positions':sum(len(p['bits']) for p in m['ports'].values() if p['direction']=='output'),'external_output_bits':len(outputs),'memory_write_cells':len(writes),'visited_cells':len(cells),'boundary_bits':len(boundary),'old_all_memory_boundary_bits':len(old),'extra_boundary_bits':extra,'extra_state_records':[{'cell':r['cell'],'type':r['type'],'extra_bits':[b for b in r['state_bits'] if b in set(extra)]} for r in state_records if any(b in set(extra) for b in r['state_bits'])],'missing_driver_bits':sorted(missing),'state_records':state_records,'input_boundary_bits':sorted(boundary&inputs),'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,P]},'scope':'Whole-cell conservative fixed point through register controls/data and combinational inputs, rooted at all external outputs and all memory write inputs. Memory array contents remain explicit separate state obligations. Measures prior cut completeness; no equivalence, init, reset-reachability or Full admission.'};D=E/'full_external_output_state_closure_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'closure_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['external_output_bits','memory_write_cells','visited_cells','boundary_bits','old_all_memory_boundary_bits','missing_driver_bits']},indent=2));print('extra_boundary_bits',len(extra))
