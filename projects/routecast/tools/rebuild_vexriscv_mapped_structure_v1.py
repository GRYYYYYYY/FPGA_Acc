"""Reconstruct original top ports and sequential cells around mapped cut logic."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'vexriscv_mapped_structure_v1_2026-10-09';D.mkdir(exist_ok=False);B=E/'vexriscv_cut_logic_v1_2026-10-09'
p=E/'vexriscv_flattened_candidate_v1_2026-10-09/design.json';m=json.loads(p.read_text())['modules']['VexRiscvSmallest'];boundary=json.loads((B/'sequential_boundary.json').read_text());assert boundary['ports']==m['ports']
proof=E/'vexriscv_cut_export_audit_v1_2026-10-09/verification.json';d=json.loads(proof.read_text());assert all(sha(p)==h for p,h in d['bindings'].items())
assert not any('init' in n.get('attributes',{}) for n in m['netnames'].values())
arch=E/'async_reset_arch_candidate_v2_2026-10-08/architecture.xml';ar=arch.with_name('receipt.json');authority=json.loads(ar.read_text());assert all(sha(p)==h for p,h in authority['bindings'].items())
models={e.get('name'):{p.get('name') for p in e.iter('port')} for e in ET.parse(arch).getroot().find('models')}
name=lambda bit:'b'+str(bit) if type(bit) is int else 'const'+bit
inputs=[];outputs=[];aliases=[]
for port,entry in m['ports'].items():
 for index,bit in enumerate(entry['bits']):
  label=port if len(entry['bits'])==1 else f'{port}[{index}]'
  (inputs if entry['direction']=='input' else outputs).append(label)
  source,target=(label,name(bit)) if entry['direction']=='input' else (name(bit),label)
  aliases.extend(['.names '+source+' '+target,'1 1'])
assert len(set(inputs+outputs))==len(inputs+outputs)
lines=['.model VexRiscvSmallest','.inputs '+' '.join(inputs),'.outputs '+' '.join(outputs)]+aliases
for line in (B/'mapped.blif').read_text().splitlines():
 if line.startswith(('.model ','.inputs ','.outputs ')) or line.strip()=='.end':continue
 lines.append(line)
counts={};records=[]
for cell_id,cell in boundary['cells'].items():
 kind=cell['type'];w={port:name(bits[0]) for port,bits in cell['connections'].items()};counts[kind]=counts.get(kind,0)+1
 if kind=='$_DFF_P_':lines.append(f".latch {w['D']} {w['Q']} re {w['C']} 2")
 else:
  assert models[kind]==set(w)=={'C','D','Q','R'}
  lines.append('.subckt '+kind+' '+' '.join(port+'='+w[port] for port in sorted(w)))
 records.append(dict(source_cell=cell_id,type=kind,ports=w))
lines.append('.end')
for kind in sorted(set(counts)-{'$_DFF_P_'}):lines.extend(['.model '+kind,'.inputs C D R','.outputs Q','.blackbox','.end'])
(D/'design.blif').write_text('\n'.join(lines)+'\n');(D/'sequential_mapping.json').write_text(json.dumps(records,indent=2)+'\n')
bindings={str(x):sha(x) for x in (Path(__file__).resolve(),p,B/'mapped.blif',B/'sequential_boundary.json',proof,arch,ar,D/'design.blif',D/'sequential_mapping.json')}
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,sequential_counts=counts,top_inputs=len(inputs),top_outputs=len(outputs),async_models_port_contract_pass=True,native_pack_tested=False,scope='Structural reconstruction for explicit experimental async-reset architecture only. Ordinary flops use rising-edge uninitialized latch; reset flops retain C/D/Q/R and PP0/PP1 primitive types. Models are blackboxes; no full HDL sequential proof, characterized reset timing or original COFFE architecture claim.'),indent=2)+'\n');print(dict(sequential_counts=counts,top_inputs=len(inputs),top_outputs=len(outputs),native_pack_tested=False),flush=True)
