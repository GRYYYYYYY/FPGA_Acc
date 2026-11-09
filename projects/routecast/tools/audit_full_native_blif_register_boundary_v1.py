"""Native-to-actual-BLIF register boundary and initialization correspondence."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_native_ram_gates_v3_2026-10-09/gates.json';B=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})))
latches={};resets={}
for line in B.read_text().replace('\\\n',' ').splitlines():
 t=line.split()
 if t and t[0]=='.latch':assert t[2] not in latches;latches[t[2]]={'D':t[1],'Q':t[2],'edge':t[3],'C':t[4],'init':t[5]}
 if len(t)>1 and t[0]=='.subckt' and t[1].startswith('$_DFF'):
  pins=dict(x.split('=',1) for x in t[2:]);assert pins['Q'] not in resets;resets[pins['Q']]={'type':t[1],'pins':pins}
init=collections.defaultdict(set)
for name,net in m['netnames'].items():
 value=net.get('attributes',{}).get('init')
 if value is not None:
  for i,b in enumerate(net['bits']):init[b].add(value[-1-i])
def net(b):return 'b'+str(b) if isinstance(b,int) else {'0':'const0','1':'const1','x':'constx'}[b]
rows=[];seen=set()
for name,c in m['cells'].items():
 if not c['type'].startswith('$_DFF'):continue
 co=c['connections'];q=co['Q'][0];qn=net(q);seen.add(qn)
 if c['type']=='$_DFF_P_':
  actual=latches.get(qn,{});expected={'D':net(co['D'][0]),'Q':qn,'edge':'re','C':net(co['C'][0])};pins=all(actual.get(p)==v for p,v in expected.items());values=init[q];assert len(values)<=1
  expected_init=next(iter(values)) if values else 'x';expected_init='2' if expected_init=='x' else expected_init;init_ok=actual.get('init')==expected_init
 else:
  actual=resets.get(qn,{});expected={p:net(bs[0]) for p,bs in co.items()};pins=actual.get('type')==c['type'] and actual.get('pins')==expected;init_ok=True
 rows.append({'native_cell':name,'native_type':c['type'],'native_q':q,'blif_q':qn,'expected':expected,'actual':actual,'boundary_pins_equal':pins,'ordinary_init_equal':init_ok,'native_init_attributes':sorted(init[q])})
coverage=seen==set(latches)|set(resets)
out={'native_registers':len(rows),'blif_latches':len(latches),'blif_reset_registers':len(resets),'matched_pins':sum(r['boundary_pins_equal'] for r in rows),'matched_init_or_reset_model':sum(r['ordinary_init_equal'] for r in rows),'complete_q_coverage':coverage,'rows':rows,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,B]},'scope':'Actual register boundary net identity and ordinary latch init/reset model correspondence only. Identical D net names do not prove the ABC combinational function driving D; no macro initialization, physical init, four-state LUT equivalence, exported Verilog or Full admission.'}
D=E/'full_native_blif_register_boundary_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'register_boundary_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['native_registers','blif_latches','blif_reset_registers','matched_pins','matched_init_or_reset_model','complete_q_coverage']},indent=2));assert coverage and all(r['boundary_pins_equal'] and r['ordinary_init_equal'] for r in rows)
