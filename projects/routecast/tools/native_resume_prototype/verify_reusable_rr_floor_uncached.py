"""Every cached epoch compared to an all-query fresh child calculation."""
import json,struct,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];w=int(sys.argv[1]);base=ROOT/f'experiments/native_resume_reusable_rr_floors_w{w}_2026-10-07';r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');assert all(sha(f)==h for f,h in r['context_bindings'].items());binary=ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor';out=base/'uncached_verification';out.mkdir(exist_ok=False)
data=(base/'context/epoch_1/queries.bin').read_bytes();magic,n,m,q=struct.unpack('<4Q',data[:32]);graph_size=8*((n+1)+m+m+n+n);graph_body=data[32:32+graph_size];assert len(data)==32+graph_size+q*24
rows=[];start=time.perf_counter()
for summary in r['rows']:
 epoch=summary['epoch'];receipt=base/f'context/epoch_{epoch}/receipt.json';assert sha(receipt)==summary['receipt_sha256'];e=json.loads(receipt.read_text());answers=e['answers'];queries=[a['query'] for a in answers];payload=out/f'epoch_{epoch}.bin';payload.write_bytes(struct.pack('<4Q',magic,n,m,len(queries))+graph_body+b''.join(struct.pack('<3Q',q['connection_id'],q['source'],q['sink']) for q in queries));file=out/f'epoch_{epoch}.jsonl'
 with file.open('w') as stream:subprocess.run([str(binary),str(payload)],stdout=stream,stderr=subprocess.PIPE,timeout=120,check=True)
 fresh=[json.loads(line) for line in file.read_text().splitlines()];expected={a['query']['connection_id']:a['minimum_integer'] for a in answers};assert len(fresh)==len(queries) and {a['connection_id']:a['minimum_integer'] for a in fresh}==expected
 rows.append(dict(epoch=epoch,connections=len(queries),all_floors_equal_fresh=True,payload_sha256=sha(payload),output_sha256=sha(file)))
(out/'verification.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(base/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,verification_seconds=time.perf_counter()-start,scope='All-query uncached child recomputation equals cache at every epoch; shared compiled algorithm and graph body, checks reuse equivalence rather than independent shortest optimality or native STA.'),indent=2)+'\n');print(w,'fresh replay parity',len(rows),'epochs',time.perf_counter()-start,flush=True)
