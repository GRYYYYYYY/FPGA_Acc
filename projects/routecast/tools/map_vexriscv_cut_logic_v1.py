"""Map combinational logic only; sequential cells preserved as explicit cut boundary."""
import json,itertools,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'vexriscv_cut_logic_v1_2026-10-09';D.mkdir(exist_ok=False)
p=E/'vexriscv_flattened_candidate_v1_2026-10-09/design.json';m=json.loads(p.read_text())['modules']['VexRiscvSmallest'];a=json.loads((E/'prospective_family_candidates_2026-10-06/frontend_availability.json').read_text());abc=Path(a['yosys_path']).parent.parent/'abc/abc';bindings={str(p):sha(p),str(abc):sha(abc),str(Path(__file__).resolve()):sha(Path(__file__))}
sequential={name:cell for name,cell in m['cells'].items() if cell['type'].startswith('$_DFF')};logic={name:cell for name,cell in m['cells'].items() if name not in sequential}
inputs=set();outputs=set()
for port in m['ports'].values():
 (inputs if port['direction']=='input' else outputs).update(port['bits'])
for cell in sequential.values():
 for port,bits in cell['connections'].items():(inputs if cell['port_directions'][port]=='output' else outputs).update(bits)
assert all(type(bit) is int or bit in ('0','1') for bit in inputs|outputs)
name=lambda bit:f'b{bit}' if type(bit) is int else f'const{bit}'
inputs={bit for bit in inputs if type(bit) is int}
lines=['.model vex_cut','.inputs '+' '.join(name(bit) for bit in sorted(inputs)),'.outputs '+' '.join(name(bit) for bit in sorted(outputs,key=str)),'.names const0','.names const1','1']
truth={'$_MUX_':(['A','B','S'],lambda v:v[1] if v[2] else v[0]),'$_NOT_':(['A'],lambda v:1-v[0]),'$_OR_':(['A','B'],lambda v:v[0]|v[1]),'$_AND_':(['A','B'],lambda v:v[0]&v[1]),'$_XOR_':(['A','B'],lambda v:v[0]^v[1])}
for cell in logic.values():
 ports,fn=truth[cell['type']];assert all(len(bits)==1 for bits in cell['connections'].values())
 args=[name(cell['connections'][port][0]) for port in ports];out=name(cell['connections']['Y'][0]);lines.append('.names '+' '.join(args+[out]))
 for vector in itertools.product((0,1),repeat=len(ports)):
  if fn(vector):lines.append(''.join(map(str,vector))+' 1')
lines.append('.end');(D/'original.blif').write_text('\n'.join(lines)+'\n');(D/'sequential_boundary.json').write_text(json.dumps(dict(cells=sequential,ports=m['ports']),indent=2)+'\n')
commands=[['read_blif original.blif; strash; if -K 6; write_blif mapped.blif','map'],['cec original.blif mapped.blif','cec']]
for file in ('original.blif','sequential_boundary.json'):bindings[str(D/file)]=sha(D/file)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,scope='All top IO and every sequential pin are explicit combinational cuts. Original sequential cells retained verbatim; no reset conversion, no reconstructed native input or full sequential equivalence claim.'),indent=2)+'\n')
for cmd,label in commands:
 with (D/(label+'.log')).open('x') as log:code=subprocess.run([str(abc),'-c',cmd],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
 assert code==0
assert 'Networks are equivalent' in (D/'cec.log').read_text()
sizes=[len(line.split())-2 for line in (D/'mapped.blif').read_text().splitlines() if line.startswith('.names ')];assert sizes and max(sizes)<=6
for file in D.iterdir():
 if file.is_file():bindings[str(file)]=sha(file)
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,mapped_nodes=len(sizes),max_lut_inputs=max(sizes),preserved_sequential_cells=len(sequential),cut_equivalence_pass=True,native_input_ready=False),indent=2)+'\n');print(dict(mapped_nodes=len(sizes),max_lut_inputs=max(sizes),preserved_sequential_cells=len(sequential),cut_equivalence_pass=True),flush=True)
