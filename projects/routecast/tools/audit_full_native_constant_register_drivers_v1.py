"""Audit constant-mapped registers without inventing initial values."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_structural_native_register_mapping_v1_2026-10-09/mapping_audit.json';F=E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json'
a=json.loads(P.read_text());m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})));rows=[]
for r in a['rows']:
 if r['status']!='constant':continue
 c=m['cells'][r['cell']];literal=r['native_candidates'][0];data=c['connections']['D'][r['lane']]
 direct=c['type']=='$dff' and data==literal
 rows.append({'cell':r['cell'],'lane':r['lane'],'q':r['bit'],'literal':literal,'type':c['type'],'data':data,'connections':c['connections'],'parameters':c['parameters'],'init_attributes':r['init_attributes'],'unconditional_capture_literal':direct,'initial_value_proven':False})
out={'rows':rows,'constant_rows':len(rows),'unconditional_literal_capture_rows':sum(r['unconditional_capture_literal'] for r in rows),'other_rows':sum(not r['unconditional_capture_literal'] for r in rows),'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,F]},'scope':'Unconditional dff with D equal literal captures it at a qualifying clock edge and preserves it thereafter. No before-first-edge initial state, event schedule, Full startup relation or enabled-register invariant is proved.'}
D=E/'full_native_constant_register_drivers_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'constant_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes']},indent=2))
