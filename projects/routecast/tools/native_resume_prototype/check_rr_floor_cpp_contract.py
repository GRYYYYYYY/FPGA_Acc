"""Independent small-graph numerical and malformed-input contract checks."""
import json,struct,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];build=ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/receipt.json';b=json.loads(build.read_text());binary=Path(b['binary']);assert sha(binary)==b['binary_sha256'];out=ROOT/'experiments/native_resume_rr_floor_cpp_contract_2026-10-07';out.mkdir(exist_ok=False)
def encode(n,offsets,dest,weights,capacity,initial,queries):
 words=[0x5243464c4f4f5231,n,len(dest),len(queries),*offsets,*dest,*weights,*capacity,*initial,*[v for q in queries for v in q]]
 return b''.join(struct.pack('<Q',v) for v in words)
base=encode(5,[0,2,3,4,4,4],[1,2,2,3],[3,5,2,1],[1]*5,[7,0,0,11,0],[(1,0,3),(2,3,3),(3,0,4)])
cases=[('tie_initial_and_unreachable',base,0,{1:13,2:11,3:None}),('zero_cycle',encode(3,[0,1,3,3],[1,0,2],[0,0,0],[1]*3,[0]*3,[(7,0,2)]),0,{7:0}),('truncated',base[:-1],2,None),('trailing',base+b'x',2,None),('out_of_range_dest',encode(2,[0,1,1],[2],[1],[1,1],[0,0],[(0,0,1)]),2,None),('disabled_endpoint',encode(2,[0,1,1],[1],[1],[1,0],[0,0],[(0,0,1)]),2,None),('overflow',encode(2,[0,1,1],[1],[(1<<64)-2],[1,1],[2,0],[(0,0,1)]),2,None)]
rows=[]
for name,payload,expected,values in cases:
 f=out/(name+'.bin');f.write_bytes(payload);r=subprocess.run([str(binary),str(f)],capture_output=True,timeout=10);assert r.returncode==expected
 if values is not None:
  actual=[json.loads(s) for s in r.stdout.decode().splitlines()];assert {x['connection_id']:x['minimum_integer'] for x in actual}==values
  if name=='tie_initial_and_unreachable':assert next(x for x in actual if x['connection_id']==1)['slots']==[1,3]
  if name=='zero_cycle':assert actual[0]['slots']==[0,2]
 rows.append(dict(case=name,exit_code=r.returncode,input_sha256=sha(f),stdout=r.stdout.decode(),stderr=r.stderr.decode()))
(out/'verification.json').write_text(json.dumps(dict(build_receipt_sha256=sha(build),binary_sha256=sha(binary),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Seven independent numerical/contract cases; not complete parser fuzzing or graph-RC model validation.'),indent=2)+'\n');print('Seven contract cases passed.')
