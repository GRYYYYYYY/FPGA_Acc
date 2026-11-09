"""Account for every BLIF RAM lane retained or pruned in actual export."""
import collections,hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_native_blif_ram_lane_pins_v1_2026-10-09/ram_pin_audit.json';F=E/'full_native_ram_gates_v3_2026-10-09/gates.json';B=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';V=E/'full_ram_init_export_runtime_v8_2026-10-09/VexRiscvFull_post_synthesis.v'
a=json.loads(P.read_text());m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})));text=V.read_text();retained=re.findall(r'dual_port_ram\s*#\(.*?\)\s*\\dual_port_ram_(\S+)\s*\(',text,re.S);assert len(retained)==len(set(retained));retained=set(retained)
nu=collections.defaultdict(list)
for name,c in m['cells'].items():
 for port,bs in c['connections'].items():
  if c['port_directions'][port]=='input':
   for bit in bs:nu[bit].append({'cell':name,'port':port})
for name,p in m['ports'].items():
 for bit in p['bits']:nu[bit].append({'top_port':name,'direction':p['direction']})
bu=collections.defaultdict(list)
for line in B.read_text().replace('\\\n',' ').splitlines():
 t=line.split()
 if not t:continue
 if t[0]=='.names':
  for net in t[1:-1]:bu[net].append({'kind':'names','output':t[-1]})
 elif t[0]=='.outputs':
  for net in t[1:]:bu[net].append({'kind':'top_output'})
 elif t[0]=='.latch':
  for net in [t[1],t[4]]:bu[net].append({'kind':'latch','Q':t[2]})
 elif t[0]=='.subckt':
  pins=dict(x.split('=',1) for x in t[2:]);output_ports={'out1','out2'} if t[1]=='dual_port_ram' else {'Q'} if t[1].startswith('$_DFF') else None
  assert output_ports is not None,t[1]
  for port,net in pins.items():
   if port not in output_ports:bu[net].append({'kind':'subckt','model':t[1],'port':port})
rows=[]
for r in a['rows']:
 pins=r['actual'];key=pins['out1'];keep=key in retained;co=m['cells'][r['native_cell']]['connections'];lane=r['lane']
 rows.append({'native_cell':r['native_cell'],'lane':lane,'blif_out1':key,'blif_out2':pins['out2'],'retained_in_export':keep,'native_output_consumers':{p:nu[co[p][lane]] for p in ['out1','out2']},'blif_output_consumers':{p:bu[pins[p]] for p in ['out1','out2']}})
pruned=[r for r in rows if not r['retained_in_export']];dead=sum(all(not u for u in [*r['native_output_consumers'].values(),*r['blif_output_consumers'].values()]) for r in pruned)
out={'source_lanes':len(rows),'export_retained_lanes':len(retained),'pruned_lanes':len(pruned),'pruned_lanes_with_no_native_or_blif_consumers':dead,'complete_export_coverage':retained=={r['blif_out1'] for r in rows if r['retained_in_export']},'rows':rows,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,F,B,V]},'scope':'Complete actual lane identity and immediate consumer inventory. Unconsumed RAM outputs cannot affect this netlist under isolated macro semantics; macro global side effects/event models and retained export transition behavior are not proved. No Full admission.'}
D=E/'full_export_pruned_ram_lanes_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'pruning_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes']},indent=2));assert out['complete_export_coverage'] and dead==len(pruned)==126 and len(retained)==174
