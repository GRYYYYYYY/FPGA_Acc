"""Actual capture operand BLIF tables and native named state aliases."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';G=R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json';m=max(json.loads(G.read_text())['modules'].values(),key=lambda m:len(m['cells']));text=B.read_text();records=[]
for node in ['new_n5324','new_n5374','new_n5375','new_n5938','new_n5939','new_n5940']:
 match=re.search(r'^\.names ([^\n]+) '+node+r'\n([^.]*)',text,re.M);assert match
 inputs=match[1].split();entries=[]
 for name in inputs:
  info={'input':name}
  if re.fullmatch(r'b\d+',name):
   bit=int(name[1:]);info['aliases']=[{'name':n,'lane':v['bits'].index(bit),'attributes':v.get('attributes',{})} for n,v in m['netnames'].items() if bit in v['bits']]
   info['direct_drivers']=[{'cell':n,'definition':c} for n,c in m['cells'].items() if bit in c['connections'].get('Q',[])]
  entries.append(info)
 records.append({'node':node,'inputs':entries,'actual_cubes':match[2].strip().splitlines()})
out={'records':records,'scope':'Actual immediate capture operand logic/state aliases. Aliases identify boundaries only, not their observed value or source/native equality. More than cache-access allow may be unknown.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [B,G]}}
D=R/'experiments/full_csr_capture_operand_aliases_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print('Archived six operand definitions with actual state aliases.')
