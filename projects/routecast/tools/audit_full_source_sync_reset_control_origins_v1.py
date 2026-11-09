"""Separate synthesized synchronous clear controls from top-level reset pins."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_source_structural_initial_obligations_v1_2026-10-09/initial_obligations.json';F=E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json';m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})));a=json.loads(P.read_text());drivers={b:(n,c,p,i) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for i,b in enumerate(bs)};primary={b:n for n,p in m['ports'].items() if p['direction']=='input' for b in p['bits']};reset_inputs={b:n for b,n in primary.items() if 'reset' in n.lower()};records=[]
for r in a['registers']:
 if not r['reset_kind'].startswith('synchronous'):continue
 n,c,p,i=drivers[r['source_bit']];root=c['connections']['SRST'][0];todo=[root];seen=set();state=set();used={};inputs=set();missing=set()
 while todo:
  b=todo.pop()
  if not isinstance(b,int) or b in seen:continue
  seen.add(b)
  if b in primary:inputs.add(b);continue
  if b not in drivers:missing.add(b);continue
  cn,cell,port,lane=drivers[b]
  if 'dff' in cell['type'].lower() or cell['type'].startswith('$memrd'):state.add(b);continue
  if cn in used:continue
  used[cn]=cell;todo.extend(bit for port,bs in cell['connections'].items() if cell['port_directions'][port]=='input' for bit in bs)
 records.append({'source_bit':r['source_bit'],'source_cell':n,'type':c['type'],'SRST_bit':root,'primary_input_ancestors':{str(b):primary[b] for b in sorted(inputs)},'top_reset_input_ancestors':{str(b):reset_inputs[b] for b in sorted(inputs&set(reset_inputs))},'state_boundaries':sorted(state),'missing_driver_bits':sorted(missing),'combinational_cells':used,'direct_top_reset':root in reset_inputs})
out={'reset_primary_inputs':{str(b):n for b,n in reset_inputs.items()},'synchronous_register_bits':len(records),'direct_top_reset_bits':sum(r['direct_top_reset'] for r in records),'combinational_top_reset_ancestor_bits':sum(bool(r['top_reset_input_ancestors']) for r in records),'without_combinational_top_reset_ancestor_bits':sum(not r['top_reset_input_ancestors'] for r in records),'enabled_reset_without_top_reset_ancestor_bits':sum(r['type']=='$sdffce' and not r['top_reset_input_ancestors'] for r in records),'records':records,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,F]},'scope':'Direct combinational dependency to named top-level reset inputs, stopping at state. Synthesized SRST may encode functional data clear rather than architectural reset. Absence of combinational reset ancestry does not exclude sequential influence through state; no initial/global equivalence or Full admission.'};D=E/'full_source_sync_reset_control_origins_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'control_origins_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['records','hashes','scope']},indent=2));assert all(not r['missing_driver_bits'] for r in records)
