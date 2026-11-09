"""Complete linear basis proof and independently CEC-verified LUT6 mapping."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];freeze=root/'experiments/gf2_recurrence_family_freeze_2026-10-06';p=json.loads((freeze/'protocol.json').read_text());r=json.loads((freeze/'receipt.json').read_text());assert r['protocol_sha256']==sha(freeze/'protocol.json');out=root/'experiments/gf2_recurrence_frontend_2026-10-06';out.mkdir();abc=next(Path(path) for path in p['native_inputs_sha256'] if Path(path).name=='abc');assert sha(abc)==p['native_inputs_sha256'][str(abc)];rows=[]
for record in r['records']:
 path=Path(record['path']);assert sha(path)==record['sha256'];lines=path.read_text().splitlines();inputs=next(x.split()[1:] for x in lines if x.startswith('.inputs '));outputs=next(x.split()[1:] for x in lines if x.startswith('.outputs '));values={name:1<<i for i,name in enumerate(inputs)};i=0;gates=0
 while i<len(lines):
  fields=lines[i].split();i+=1
  if not fields or fields[0]!='.names':continue
  source=fields[1:-1];target=fields[-1];table=[]
  while i<len(lines) and not lines[i].startswith('.'):table.append(lines[i]);i+=1
  assert target not in values and all(n in values for n in source)
  if len(source)==1 and table==['1 1']:values[target]=values[source[0]]
  elif len(source)==2 and set(table)=={'01 1','10 1'}:values[target]=values[source[0]]^values[source[1]]
  else:raise ValueError('generator has non-linear/unrecognized gate')
  gates+=1
 width=record['width'];bits=p['state_bits'];mask=sum(1<<bit for bit in p['tap_indices']);limit=(1<<bits)-1;expected=[0]*bits
 # Integer recurrence oracle; complete basis suffices because every gate above
 # was proved to be a homogeneous linear map, not merely sampled as such.
 for basis in range(bits+width):
  state=1<<basis if basis<bits else 0;data=0 if basis<bits else 1<<(basis-bits)
  for step in range(width):
   feedback=((state>>(bits-1))^(data>>step))&1;state=(state<<1)&limit
   if feedback:state^=mask
  for bit in range(bits):
   if (state>>bit)&1:expected[bit]|=1<<basis
 assert [values[n] for n in outputs]==expected
 directory=out/f'gf2_d{width}';directory.mkdir();(directory/'oracle.json').write_text(json.dumps({'all_gates_homogeneous_linear':True,'complete_basis_vectors':bits+width,'zero_vector_preserved':True,'output_matrix':expected,'generated_sha256':sha(path),'scope':'Complete linear-equivalence proof to independent integer recurrence; not random-only functional sampling.'},indent=2)+'\n');phases=[]
 for stage,command in [('map',[str(abc),'-c',f'read_blif {path}; strash; if -K 6; write_blif design.blif']),('cec',[str(abc),'-c',f'cec {path} design.blif'])]:
  t=time.monotonic()
  with (directory/(stage+'.log')).open('w') as stream:code=subprocess.run(command,cwd=directory,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
  assert code==0
  phases.append({'stage':stage,'command':command,'wall_s':time.monotonic()-t,'exit_code':code})
 assert 'Networks are equivalent' in (directory/'cec.log').read_text();mapped=(directory/'design.blif').read_text();sizes=[len(line.split())-2 for line in mapped.splitlines() if line.startswith('.names ')];assert sizes and max(sizes)<=6
 row={'width':width,'generator_gates':gates,'mapped_luts':len(sizes),'complete_linear_basis_proof':True,'ABC_CEC_equivalent':True,'phases':phases,'files_sha256':{str(f):sha(f) for f in directory.iterdir() if f.is_file()}};rows.append(row);print(width,'basis proved','LUTs',len(sizes),flush=True)
(out/'receipt.json').write_text(json.dumps({'freeze_receipt_sha256':sha(freeze/'receipt.json'),'source_sha256':sha(Path(__file__)),'rows':rows,'all_variants_retained':True,'native_started':False},indent=2)+'\n')
