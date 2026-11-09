"""Check all native uses of unresolved register alias candidates."""
import collections
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
mp=ROOT/'experiments/full_structural_native_register_mapping_v1_2026-10-09/mapping_audit.json'
np=ROOT/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json'
audit=json.loads(mp.read_text())
m=max(json.loads(np.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})))
uses=collections.defaultdict(list)
for name,c in m['cells'].items():
 for port,bits in c['connections'].items():
  for lane,bit in enumerate(bits):
   uses[bit].append({'cell':name,'type':c['type'],'port':port,'direction':c['port_directions'][port],'lane':lane})
ports=collections.defaultdict(list)
for name,p in m['ports'].items():
 for lane,bit in enumerate(p['bits']): ports[bit].append({'port':name,'lane':lane,'direction':p['direction']})
rows=[]
for row in audit['rows']:
 if row['status']!='unresolved': continue
 candidates=row['native_candidates']
 rows.append({'structural_cell':row['cell'],'structural_lane':row['lane'],'aliases':row['aliases'],'candidates':candidates,'cell_uses':[u for bit in candidates for u in uses[bit]],'top_port_uses':[u for bit in candidates for u in ports[bit]]})
unused=sum(bool(r['candidates']) and not r['cell_uses'] and not r['top_port_uses'] for r in rows)
report={'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [mp,np]},'unresolved_rows':len(rows),'unused_native_alias_rows':unused,'remaining_used_or_missing_candidates':len(rows)-unused,'scope':'Native connectivity only: dead named wires have no cell or top-port use. This is not a proof that source state was safely eliminated; that requires source/intermediate influence or transition equivalence.','rows':rows}
out=ROOT/'experiments/full_native_unresolved_state_usage_v1_2026-10-09';out.mkdir(exist_ok=True)
(out/'usage_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
assert unused==len(rows), 'Some candidates require further connectivity tracing'
