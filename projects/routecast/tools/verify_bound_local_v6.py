"""Independent original-graph all-arc bound certificates and paired byte audit."""
import json,sys,struct,subprocess,hashlib
from array import array
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/bound_local_cost_v6_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');binary=R/'build/cache_bound_certificate_v2_2026-10-07/check';cpp=R/'tools/cache_bound_certificate_cpp/main_v2.cpp';bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(out/'protocol.json'):sha(out/'protocol.json'),str(binary):sha(binary),str(cpp):sha(cpp)};assert all(sha(k)==h for k,h in bindings.items())
ep=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip/endpoints.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);gf=out/'certificate_graph.bin'
with gf.open('wb') as stream:
 stream.write(struct.pack('<3Q',2026100706,len(nodes),len(f['edge_ids'])))
 for seq in (f['row_offsets'],f['dest_ranks'],f['capacities'],rc.increments):
  values=array('Q',seq)
  if sys.byteorder!='little':values.byteswap()
  stream.write(values.tobytes())
bindings[str(gf)]=sha(gf);h=hashlib.sha256()
for seq in (f['row_offsets'],f['dest_ranks'],f['capacities'],rc.increments,[rc.initial(n) for n in range(len(nodes))]):
 for value in seq:h.update(struct.pack('<Q',value))
reference=None;arguments=[]
for row in r['rows']:
 cp=out/f"{row['repeat']}_{row['version']}_cache.json";c=json.loads(cp.read_text());bindings[str(cp)]=sha(cp);assert c['graph_sha256']==digest and c['model_sha256']==h.hexdigest() and c['closed'] and not c['invalid'] and c['close_proof']['initial_and_final_content_digest_equal'];assert c['cutoff_integer']==rc.scale//(2*10**9)
 signatures=[]
 for event in c['events']:
  file=Path(event['path']);assert sha(file)==event['sha256'];bindings[str(file)]=event['sha256'];data=file.read_bytes();assert len(data)==8*len(nodes);values=struct.unpack('<'+str(len(nodes))+'Q',data);assert values[event['sink']]==0 and all(v<=c['cutoff_integer'] for v in values);signatures.append((event['sink'],sha(file)))
  if reference is None:arguments.append(str(event['sink'])+':'+str(file))
 if reference is None:reference=signatures
 else:assert signatures==reference
 assert c['misses']==c['hits']==len(reference)==178 and c['aborted']==1 and c['evictions']==0
proof=json.loads(subprocess.run([str(binary),str(gf),*arguments],capture_output=True,text=True,check=True).stdout);assert proof['certificates']==178
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(all_eight_publication_sets_exact=True,independent_model_and_range_checks=True,compiled_certificate=proof,bindings=bindings),indent=2)+'\n');print('PASS eight byte-identical sets and178 independent all-arc certificates',flush=True)
