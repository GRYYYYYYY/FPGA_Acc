"""Match actual one-bit logical AND guards to native AND gates."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';paths=[E/'full_guarded_pending_shared_groups_v1_2026-10-09/guarded_audit.json',E/'full_guarded_pending_native_capture_v1_2026-10-09/native_capture_audit.json',E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json',E/'full_native_ram_gates_v3_2026-10-09/gates.json']
a,b=[json.loads(p.read_text()) for p in paths[:2]];s,n=[max(json.loads(p.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{}))) for p in paths[2:]]
aliases=collections.defaultdict(set)
for name,v in s['netnames'].items():
 if name in n['netnames'] and len(v['bits'])==len(n['netnames'][name]['bits']):
  for x,y in zip(v['bits'],n['netnames'][name]['bits']):aliases[x].add(y)
def drivers(m):return {bit:(name,c,p,i) for name,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for i,bit in enumerate(bs)}
sd,nd=drivers(s),drivers(n);checks={};groups=[]
byq={r['native_q']:r for r in b['rows']}
for g in a['rows']:
 native=byq[g['native_q']];passed=True
 for member in g['members']:
  for pw in member.get('pw_bindings',[]):
   target=next(x for x in native['pending_write_checks'] if x['alias']==pw['pw_alias'])
   if target['guard_pin_equal']:continue
   key=pw['pw_alias'];sg=member['guard'];ng=target['D'][0]
   sn,sc,sp,si=sd[sg];nn,nc,np,ni=nd[ng]
   mappings={port:sorted(aliases[sc['connections'][port][0]],key=str) for port in ['A','B']} if sc['type']=='$logic_and' and all(len(sc['connections'][p])==1 for p in ['A','B']) else {}
   valid=bool(mappings) and nc['type']=='$_AND_' and all(mappings[p]==nc['connections'][p] for p in ['A','B']) and target['same_clock'] and target['init']=='0' and target['type']=='$_DFF_P_'
   checks[key]={'structural_guard':sg,'native_guard':ng,'structural_cell':sn,'native_cell':nn,'structural_connections':sc['connections'],'native_connections':nc['connections'],'operand_aliases':mappings,'conditional_cone_identity':valid}
   passed=passed and valid
 groups.append({'native_q':g['native_q'],'guard_boundary_correspondence':passed,'data_clock_pin_correspondence':native['data_pin_equal'] and native['clock_pin_equal']})
out={'unique_missing_guard_cones':len(checks),'matched_guard_cones':sum(c['conditional_cone_identity'] for c in checks.values()),'groups':groups,'checks':checks,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'scope':'Actual one-bit logical AND is the same Boolean/four-state AND as native $_AND_ under explicit equality of the two named operand boundary signals. Upstream mask/valid cone equivalence is not proved; no ABC/export or Full admission. Local known-one guarded native capture remains conditional on selected-input and boundary signal relations.'}
D=E/'full_pending_native_guard_cones_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'guard_cone_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'unique_missing_guard_cones':len(checks),'matched_guard_cones':out['matched_guard_cones'],'guarded_capture_groups':sum(r['guard_boundary_correspondence'] and r['data_clock_pin_correspondence'] for r in groups)},indent=2))
assert all(c['conditional_cone_identity'] for c in checks.values()) and all(g['guard_boundary_correspondence'] and g['data_clock_pin_correspondence'] for g in groups)
