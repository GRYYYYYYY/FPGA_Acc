"""Real binary positive and malformed admissibility witnesses."""
import json,struct,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/cache_certificate_cpp_contract_v2_2026-10-07';out.mkdir();binary=R/'build/cache_bound_certificate_v2_2026-10-07/check';graph=out/'graph.bin';values=[2026100706,3,2,0,1,2,2,1,2,1,1,1,2,3];graph.write_bytes(struct.pack('<'+str(len(values))+'Q',*values));bound=out/'bound.bin';bound.write_bytes(struct.pack('<3Q',5,3,0));r=subprocess.run([str(binary),str(graph),'2:'+str(bound)],capture_output=True,text=True);assert r.returncode==0
rows=[]
for name,data in [('inequality',struct.pack('<3Q',6,3,0)),('domain',struct.pack('<3Q',(1<<64)-1,3,0)),('target',struct.pack('<3Q',5,3,1)),('truncated',b'zero'),('trailing',struct.pack('<3Q',5,3,0)+b'x')]:
 p=out/(name+'.bin');p.write_bytes(data);r=subprocess.run([str(binary),str(graph),'2:'+str(p)],capture_output=True,text=True);assert r.returncode!=0;rows.append(dict(name=name,error=r.stderr.strip()))
(out/'receipt.json').write_text(json.dumps(dict(valid_certificate_pass=True,rejections=rows,bindings={str(binary):sha(binary),str(R/'tools/cache_bound_certificate_cpp/main_v2.cpp'):sha(R/'tools/cache_bound_certificate_cpp/main_v2.cpp'),str(Path(__file__)):sha(__file__)},scope='Private admissibility checker framing/domain/inequality contract, not router correctness.'),indent=2)+'\n');print('PASS')
