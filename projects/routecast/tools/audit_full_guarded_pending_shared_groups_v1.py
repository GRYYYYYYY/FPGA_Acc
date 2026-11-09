"""Actual pending-lane capture certificates under known-one write enable."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_native_shared_register_updates_v1_2026-10-09/update_audit.json';A=E/'full_native_shared_register_constant_related_expressions_v1_2026-10-09/expression_audit.json';F=E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json'
groups=json.loads(P.read_text())['records'];bad={r['native_q'] for r in json.loads(A.read_text())['records'] if not r['expression_identity']};m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})))
d={b:(n,c,p,i) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for i,b in enumerate(bs)}
def guard_input(b):
 if b not in d:return b
 _,c,p,i=d[b]
 if c['type']=='$mux' and c['connections']['A']==['0'] and c['connections']['B']==['1']:return c['connections']['S'][0]
 return b
rows=[]
for g in groups:
 if g['native_q'] not in bad:continue
 members=[];common=[]
 baseline=m['cells'][g['members'][0]['cell']]
 for r in g['members']:
  c=m['cells'][r['cell']];b=c['connections']['D'][r['lane']];driver=d.get(b);entry={'cell':r['cell'],'lane':r['lane'],'data_input':b,'same_unconditional_clock':c['type']=='$dff' and baseline['type']=='$dff' and c['connections']['CLK']==baseline['connections']['CLK'] and int(c['parameters']['CLK_POLARITY'],2)==int(baseline['parameters']['CLK_POLARITY'],2)}
  if driver and driver[1]['type']=='$mux':
   _,mux,p,i=driver;co=mux['connections'];selected=co['B'][i];guard=co['S'][0]
   aliases=[n for n,v in m['netnames'].items() if r['q'] in v['bits'] and (n.endswith('.pa') or n.endswith('.pd'))]
   matches=[]
   for n in aliases:
    pw=n.rsplit('.',1)[0]+'.pw'
    if pw not in m['netnames']:continue
    bit=m['netnames'][pw]['bits'][0];pc=d[bit][1]
    same=pc['type']=='$dff' and guard_input(pc['connections']['D'][0])==guard and pc['connections']['CLK']==c['connections']['CLK'] and int(pc['parameters']['CLK_POLARITY'],2)==int(c['parameters']['CLK_POLARITY'],2)
    matches.append({'pw_alias':pw,'pw_q':bit,'pw_D':pc['connections']['D'][0],'same_capture_guard':same,'init':m['netnames'][pw].get('attributes',{}).get('init')})
   entry.update({'selected_data':selected,'guard':guard,'inactive_data':co['A'][i],'pw_bindings':matches,'guard_certificate':bool(matches) and all(v['same_capture_guard'] and v['init']=='0' for v in matches)})
   common.append(selected)
  else:entry.update({'selected_data':b,'unguarded_member':True});common.append(b)
  members.append(entry)
 valid=all(r['same_unconditional_clock'] for r in members) and len(set(common))==1 and all(r.get('guard_certificate',r.get('unguarded_member',False)) for r in members)
 rows.append({'native_q':g['native_q'],'same_selected_data':len(set(common))==1,'guarded_capture_certificate':valid,'members':members})
out={'groups':len(rows),'certified_groups':sum(r['guarded_capture_certificate'] for r in rows),'rows':rows,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,A,F]},'scope':'Known-one pw after a qualifying edge implies pending lane captured common B data, because pw D and mux select share the actual net. Initialized pw=0 makes this guarded equality initially vacuous. This certifies local intermediate pending capture only, not native capture, macro observational equivalence, X-enable behavior, Full startup, or global relational induction.'}
D=E/'full_guarded_pending_shared_groups_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'guarded_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'groups':out['groups'],'certified_groups':out['certified_groups']},indent=2))
assert out['certified_groups']==out['groups']
