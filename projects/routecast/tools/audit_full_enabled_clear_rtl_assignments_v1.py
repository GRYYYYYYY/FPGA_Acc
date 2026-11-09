"""Archive original RTL assignment sites for actual enabled synchronous-clear lanes."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
F=E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json';A=E/'full_source_sync_reset_control_origins_v1_2026-10-09/control_origins_audit.json';V=E/'full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v'
m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));lines=V.read_text().splitlines();records=[]
for r in json.loads(A.read_text())['records']:
 if r['type']!='$sdffce':continue
 b=r['source_bit'];aliases=[];sites=[]
 for name,net in m['netnames'].items():
  if b not in net['bits']:continue
  aliases.append({'name':name,'lane':net['bits'].index(b)})
  # Hierarchical aliases refer to submodule-local original identifiers.
  ident=name.rsplit('.',1)[-1]
  if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',ident):continue
  pattern=re.compile(r'^\s*'+re.escape(ident)+r'(?:\s*\[[^]]+\])?\s*<=')
  for i,line in enumerate(lines):
   if pattern.search(line):
    start=max(j for j in range(i+1) if re.search(r'^\s*always\s*@',lines[j]))
    sites.append({'alias':name,'line':i+1,'always_line':start+1,'always_header':lines[start].strip(),'assignment':line.strip(),'preceding_context':lines[max(start,i-9):i]})
 # Dedupe actual sites; preserve all aliases in separate inventory.
 unique={s['line']:s for s in sites}
 assert unique, (b,aliases)
 records.append({'source_bit':b,'source_cell':r['source_cell'],'aliases':aliases,'assignment_sites':list(unique.values())})
assert len(records)==12
out={'enabled_functional_clear_bits':12,'records':records,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,A,V]},'scope':'Exact textual original assignment inventory, not a Verilog control-flow proof. Context and always headers support manual inspection; does not prove startup enable values, overwrite coverage, reachability, or Full equivalence.'}
d=E/'full_enabled_clear_rtl_assignments_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'assignment_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{'bit':r['source_bit'],'sites':[(s['line'],s['assignment'],s['always_header']) for s in r['assignment_sites']]} for r in records],indent=2))
