"""All lazy bounds of successful local joint trial, independent fingerprint/C++ arcs."""
import sys,json,struct,hashlib,subprocess
from array import array
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_continuation_net_window_joint_v1_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());binary=R/'build/cache_bound_certificate_v2_2026-10-07/check';cpp=R/'tools/cache_bound_certificate_cpp/main_v2.cpp';bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(binary):sha(binary),str(cpp):sha(cpp),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(k)==v for k,v in bindings.items());(out/'bound_verification_protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n');graph,digest,nodes,f,rc,_=load_endpoints(base/'endpoints.json');cache=json.loads((out/'cache_receipt.json').read_text());h=hashlib.sha256()
for values in (f['row_offsets'],f['dest_ranks'],f['capacities'],rc.increments,[rc.initial(n) for n in range(len(nodes))]):
 for value in values:h.update(struct.pack('<Q',value))
assert h.hexdigest()==cache['model_sha256'] and cache['graph_sha256']==digest and cache['closed'] and not cache['invalid'];graphfile=out/'certificate_graph.bin'
with graphfile.open('wb') as stream:
 stream.write(struct.pack('<3Q',2026100706,len(nodes),len(f['edge_ids'])))
 for values in (f['row_offsets'],f['dest_ranks'],f['capacities'],rc.increments):
  data=array('Q',values)
  if sys.byteorder!='little':data.byteswap()
  stream.write(data.tobytes())
assert graphfile.read_bytes()==(out/'bounds/worker_graph.bin').read_bytes() and cache['worker_closed']
for asset,asset_digest in cache['worker_assets'].items():assert sha(asset)==asset_digest;bindings[asset]=asset_digest
args=[]
for event in cache['events']:
 file=Path(event['path']);assert sha(file)==event['sha256'];data=file.read_bytes();assert len(data)==8*len(nodes);d=struct.unpack('<'+str(len(nodes))+'Q',data);assert d[event['sink']]==0 and all(x<=rc.scale//(2*10**9) for x in d);args.append(str(event['sink'])+':'+str(file))
proof=json.loads(subprocess.run([str(binary),str(graphfile),*args],check=True,text=True,capture_output=True).stdout);assert proof['certificates']==len(cache['events'])==cache['misses'];assert cache['evictions']==max(0,len(args)-cache['max_entries']);assert cache['retained_distance_bytes']==min(len(args),cache['max_entries'])*8*len(nodes);assert all(sha(k)==v for k,v in bindings.items());(out/'bound_verification.json').write_text(json.dumps(dict(bindings=bindings,certificate_graph_sha256=sha(graphfile),proof=proof,model_fingerprint_exact=True,all_archived_bounds_admissible=True,scope='Original graph lower-bound admissibility, retained under additional node prohibitions; no native proof.'),indent=2)+'\n');print('PASS bounds',len(args))
