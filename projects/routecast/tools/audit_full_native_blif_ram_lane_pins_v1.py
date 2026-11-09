"""Actual scalar BLIF RAM lane expansion and literal pin preservation."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_native_ram_gates_v3_2026-10-09/gates.json';B=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})));records={};lines=B.read_text().replace('\\\n',' ').splitlines();tables={};i=0
while i<len(lines):
 t=lines[i].split();i+=1
 if len(t)>1 and t[:2]==['.subckt','dual_port_ram']:
  pins=dict(x.split('=',1) for x in t[2:]);assert pins['out1'] not in records;records[pins['out1']]=pins
 if t and t[0]=='.names':
  rows=[]
  while i<len(lines) and not lines[i].lstrip().startswith('.'):
   row=lines[i].split();i+=1
   if row and not row[0].startswith('#'):rows.append(row)
  tables[t[-1]]={'inputs':t[1:-1],'rows':rows}
def net(b):return 'b'+str(b) if isinstance(b,int) else {'0':'const0','1':'const1','x':'constx'}[b]
rows=[];omitted=[];seen=set();literal_counts=collections.Counter()
for name,c in m['cells'].items():
 if c['type']!='dual_port_ram':continue
 co=c['connections']
 for lane,out in enumerate(co['out1']):
  key=net(out)
  if key not in records:
   omitted.append({'native_cell':name,'lane':lane,'data1':co['data1'][lane],'data2':co['data2'][lane],'out1':out,'out2':co['out2'][lane]});continue
  seen.add(key);expected={p:net(co[p][lane]) for p in ['data1','data2','out1','out2']}
  expected.update({p:net(co[p][0]) for p in ['clk','we1','we2']})
  for p in ['addr1','addr2']:
   expected.update({f'{p}[{i}]':net(b) for i,b in enumerate(co[p])})
  literal_counts.update(v for p,v in expected.items() if p not in ['out1','out2'] and v.startswith('const'))
  rows.append({'native_cell':name,'lane':lane,'expected':expected,'actual':records[key],'pins_equal':expected==records[key]})
assert tables['const0'] in [{'inputs':[],'rows':[]},{'inputs':[],'rows':[['0']]}] and tables['const1']=={'inputs':[],'rows':[['1']]}
# An omitted output may be used by unrelated names; inspect actual cell and top-port consumers.
used={b for c in m['cells'].values() for p,bs in c['connections'].items() if c['port_directions'][p]=='input' for b in bs};used.update(b for p in m['ports'].values() for b in p['bits'])
for r in omitted:r['outputs_unused']=r['out1'] not in used and r['out2'] not in used
out={'scalar_blif_lanes':len(records),'matched_native_lanes':len(rows),'matched_pins':sum(r['pins_equal'] for r in rows),'complete_scalar_lane_coverage':seen==set(records),'literal_input_pin_counts':dict(literal_counts),'omitted_native_lanes':omitted,'rows':rows,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,B]},'scope':'Actual native 20-bit macros to retained scalar BLIF RAM lanes, exact data/address/clock/we/output pins and literal constant definitions. Unused omitted lanes recorded. Does not prove scalar macro memory content/init, event order, full exported model behavior or Full admission.'}
D=E/'full_native_blif_ram_lane_pins_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'ram_pin_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'scalar_blif_lanes':len(records),'matched_pins':out['matched_pins'],'complete_coverage':out['complete_scalar_lane_coverage'],'literal_input_pin_counts':out['literal_input_pin_counts'],'omitted_native_lanes':len(omitted),'unused_omitted_lanes':sum(r['outputs_unused'] for r in omitted)},indent=2));assert out['complete_scalar_lane_coverage'] and all(r['pins_equal'] for r in rows) and all(r['outputs_unused'] for r in omitted)
