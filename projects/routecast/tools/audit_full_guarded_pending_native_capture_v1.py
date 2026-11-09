"""Check actual native D/clock and pending-write guard pin correspondence."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';paths=[E/'full_guarded_pending_shared_groups_v1_2026-10-09/guarded_audit.json',E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json',E/'full_native_ram_gates_v3_2026-10-09/gates.json']
a=json.loads(paths[0].read_text());s,n=[max(json.loads(p.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{}))) for p in paths[1:]]
aliases=collections.defaultdict(set)
for name,v in s['netnames'].items():
 if name in n['netnames'] and len(v['bits'])==len(n['netnames'][name]['bits']):
  for x,y in zip(v['bits'],n['netnames'][name]['bits']):aliases[x].add(y)
d=collections.defaultdict(list)
for k,c in n['cells'].items():
 if c['type'].startswith('$_DFF'):
  for b in c['connections']['Q']:d[b].append((k,c))
rows=[]
for g in a['rows']:
 assert len(d[g['native_q']])==1
 name,c=d[g['native_q']][0];selected=g['members'][0]['selected_data'];data_candidates=sorted(aliases[selected],key=str);clock=s['cells'][g['members'][0]['cell']]['connections']['CLK'][0]
 checks=[]
 for member in g['members']:
  for pw in member.get('pw_bindings',[]):
   net=n['netnames'][pw['pw_alias']];q=net['bits'][0];pc=d[q];assert len(pc)==1
   pn,pg=pc[0];guard_candidates=sorted(aliases[member['guard']],key=str)
   checks.append({'alias':pw['pw_alias'],'native_pw_q':q,'native_cell':pn,'type':pg['type'],'D':pg['connections']['D'],'guard_candidates':guard_candidates,'guard_pin_equal':guard_candidates==pg['connections']['D'],'init':net.get('attributes',{}).get('init'),'same_clock':pg['connections'].get('C')==c['connections'].get('C')})
 row={'native_q':g['native_q'],'native_cell':name,'native_type':c['type'],'native_connections':c['connections'],'selected_data_candidates':data_candidates,'data_pin_equal':data_candidates==c['connections']['D'],'clock_pin_equal':sorted(aliases[clock],key=str)==c['connections'].get('C'),'pending_write_checks':checks}
 row['all_pin_checks']=row['data_pin_equal'] and row['clock_pin_equal'] and c['type']=='$_DFF_P_' and all(x['guard_pin_equal'] and x['same_clock'] and x['type']=='$_DFF_P_' and x['init']=='0' for x in checks)
 rows.append(row)
out={'groups':len(rows),'passed_pin_groups':sum(r['all_pin_checks'] for r in rows),'rows':rows,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'scope':'Actual pre-ABC native register pin correspondence and known-one guarded capture, conditional on selected-data/guard boundary signal correspondence. Alias identity does not prove upstream combinational function equivalence. No ABC/export, X-enable, macro event ordering or Full functional admission.'}
D=E/'full_guarded_pending_native_capture_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'native_capture_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'groups':out['groups'],'passed_pin_groups':out['passed_pin_groups']},indent=2))
assert all(r['data_pin_equal'] and r['clock_pin_equal'] for r in rows), 'Selected-data or clock pin mapping failed'
# Missing guard aliases are unresolved obligations, not an inequivalence result.
