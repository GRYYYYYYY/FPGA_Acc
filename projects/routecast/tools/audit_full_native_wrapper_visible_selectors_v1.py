"""Check every retained actual native wrapper q lane and selector pins."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_native_ram_gates_v3_2026-10-09/gates.json';m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})))
drivers=collections.defaultdict(list)
for name,c in m['cells'].items():
 for p,bits in c['connections'].items():
  if c['port_directions'][p]=='output':
   for b in bits:drivers[b].append((name,c))
uses=collections.defaultdict(list)
for name,c in m['cells'].items():
 for p,bits in c['connections'].items():
  if c['port_directions'][p]=='input':
   for b in bits:uses[b].append((name,p))
ports={b for p in m['ports'].values() for b in p['bits']}
rows=[];skipped=[];slices=[]
for alias,net in m['netnames'].items():
 if not alias.endswith('.q'):continue
 prefix=alias[:-1]
 if not all(prefix+x in m['netnames'] for x in ['er','hit','raw','held','fwd']):continue
 slices.append(prefix[:-1]);v={x:m['netnames'][prefix+x]['bits'] for x in ['er','hit','raw','held','fwd']}
 for lane,q in enumerate(net['bits']):
  if q not in drivers:
   skipped.append({'slice':prefix[:-1],'lane':lane,'q':q,'no_cell_use':not uses[q],'no_top_port':q not in ports});continue
  assert len(drivers[q])==1
  name,outer=drivers[q][0];oc=outer['connections'];innerbit=oc.get('B',[None])[0];pairs=drivers.get(innerbit,[])
  inner=pairs[0][1] if len(pairs)==1 else {};ic=inner.get('connections',{})
  expected_outer={'A':[v['held'][lane]],'S':v['er']};expected_inner={'A':[v['raw'][lane]],'B':[v['fwd'][lane]],'S':v['hit']}
  selector_ok=outer['type']=='$_MUX_' and inner.get('type')=='$_MUX_' and all(oc[p]==bs for p,bs in expected_outer.items()) and all(ic[p]==bs for p,bs in expected_inner.items())
  heldpairs=drivers[v['held'][lane]];held=heldpairs[0][1] if len(heldpairs)==1 else {};held_ok=held.get('type')=='$_DFF_P_' and held['connections']['D']==[q]
  rows.append({'slice':prefix[:-1],'lane':lane,'q':q,'outer_cell':name,'outer_connections':oc,'inner_cell':pairs[0][0] if pairs else None,'inner_connections':ic,'selector_pins_equal':selector_ok,'held_D_equals_q':held_ok})
out={'slices':slices,'retained_lanes':len(rows),'selector_matches':sum(r['selector_pins_equal'] for r in rows),'held_capture_matches':sum(r['held_D_equals_q'] for r in rows),'skipped_dead_lanes':skipped,'rows':rows,'input_sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'scope':'Actual pre-ABC native retained q equals er ? (hit ? fwd : raw) : held by exact two-mux pins; actual held captures q. This establishes combinational selector structure, including native mux four-state semantics, but not equality of the selected boundary states, init, macro scheduling, ABC/export or Full admission.'}
D=E/'full_native_wrapper_visible_selectors_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'selector_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'slices':len(slices),'retained_lanes':len(rows),'selector_matches':out['selector_matches'],'held_capture_matches':out['held_capture_matches'],'dead_lanes':len(skipped)},indent=2));assert all(r['selector_pins_equal'] and r['held_D_equals_q'] for r in rows) and all(r['no_cell_use'] and r['no_top_port'] for r in skipped)
