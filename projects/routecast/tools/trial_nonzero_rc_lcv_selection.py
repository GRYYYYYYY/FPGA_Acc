"""Export exact finite binary constraints and run bounded isolated C++ solver."""
import json,subprocess,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_pair_avoidance_2026-10-06';out=root/'experiments/nonzero_rc_lcv_selection_2026-10-06';out.mkdir();r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json');graph,digest,_,f,_,queries,_=load(root);groups=r['candidates'];keys=[tuple(g['key']) for g in groups];paths=[g['paths'] for g in groups];feet=[[set(p['nodes']) for p in ps] for ps in paths];parents=[[{n:(u,e) for n,u,e in p['parents']} for p in ps] for ps in paths];owners=defaultdict(set)
for i,ps in enumerate(feet):
 for p in ps:
  for n in p:owners[n].add(keys[i][0])
# Under this condition no capacity>1 resource creates an unrepresented higher-order constraint.
assert all(f['capacities'][n]==1 or f['capacities'][n]>=len(nets) for n,nets in owners.items())
assert all(0<len(ps)<=63 for ps in paths)
(out/'protocol.json').write_text(json.dumps({'state_limit':200000,'parent_sha256':sha(parent/'receipt.json'),'logged_isolation_events':256,'policy':'Fix universally compatible residual variables to lowest candidate then C++ AC3/MRV unresolved-degree ties and descending total neighbor domain support candidates, candidateID ties; graph-derived pair compatibility; assert all resource capacity constraints are binary or universally unconstraining','scope':'FOUND independently audited; exhaustion not certified UNSAT; compiler/export/search cost not measured as full routing benefit'},indent=2)+'\n')
values=[str(len(keys)),str(200000),*[str(len(ps)) for ps in paths]]
for i in range(len(keys)):
 for j in range(len(keys)):
  if i==j:continue
  for a,p in enumerate(feet[i]):
   mask=0
   for b,q in enumerate(feet[j]):
    valid=all(f['capacities'][n]>=(1 if keys[i][0]==keys[j][0] else 2) for n in p&q)
    if keys[i][0]==keys[j][0]:valid=valid and all(parents[i][a][n]==parents[j][b][n] for n in parents[i][a].keys()&parents[j][b].keys())
    if valid:mask|=1<<b
   values.append(str(mask))
input_path=out/'constraints.txt';input_path.write_text(' '.join(values)+'\n');source=root/'tools/native_candidate_selection/lcv_search.cpp';binary=out/'search';subprocess.run(['g++','-O2','-std=c++17',str(source),'-o',str(binary)],check=True);start=time.monotonic()
with input_path.open() as stream:result=subprocess.run([str(binary),str(out/'isolation.tsv')],stdin=stream,capture_output=True,text=True,check=True)
elapsed=time.monotonic()-start;(out/'stdout.txt').write_text(result.stdout);parts=result.stdout.split();status=parts[0];states=int(parts[1]);selected=list(map(int,parts[2:])) if status=='FOUND' else None
receipt={'isolation_fixes':int(result.stderr.split()[-1]),'isolation_log_sha256':sha(out/'isolation.tsv'),'status':status,'states':states,'selected':selected,'search_process_seconds':elapsed,'parent_sha256':sha(parent/'receipt.json'),'constraints_sha256':sha(input_path),'cpp_sha256':sha(source),'binary_sha256':sha(binary),'python_sha256':sha(Path(__file__)),'protocol_sha256':sha(out/'protocol.json')};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(status,'states',states,'search seconds',elapsed)
