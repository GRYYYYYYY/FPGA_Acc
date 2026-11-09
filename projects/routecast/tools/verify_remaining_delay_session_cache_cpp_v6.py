"""Independently certify every archived sink bound, including evicted entries."""
import json,sys,struct,hashlib,subprocess
from array import array
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/mcnc_bounded_owner_session_cache_v7_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');binary=R/'build/cache_bound_certificate_v2_2026-10-07/check';cpp=R/'tools/cache_bound_certificate_cpp/main_v2.cpp';bindings={str(binary):sha(binary),str(cpp):sha(cpp),**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(path)==h for path,h in bindings.items());(out/'cache_cpp_v3_verification_protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Every archived cache publication, including evictions. Independent model fingerprint, all positive-capacity predecessor closure/Bellman inequality, target zero, byte accounting, timeout publication count. These certify admissibility; not full optimality for arbitrary unavailable regions.'))+'\n');rows=[];INF=(1<<64)-1
for row in r['rows']:
 name=row['name'];graph,digest,nodes,f,rc,queries=load_endpoints(base/name/'endpoints.json');cache=json.loads((out/name/'cache_receipt.json').read_text());assert cache['closed'] and not cache['invalid'] and cache['close_proof']['initial_and_final_content_digest_equal'];assert cache==row['cache_summary'] and cache['graph_sha256']==digest;h=hashlib.sha256()
 for seq in (f['row_offsets'],f['dest_ranks'],f['capacities'],rc.increments,[rc.initial(n) for n in range(len(nodes))]):
  for value in seq:h.update(struct.pack('<Q',value))
 assert h.hexdigest()==cache['model_sha256'];certified=0;below_cap=0;total_values=0;arguments=[];graphfile=out/name/'certificate_graph.bin'
 with graphfile.open('wb') as stream:
  stream.write(struct.pack('<3Q',2026100706,len(nodes),len(f['edge_ids'])))
  for values in (f['row_offsets'],f['dest_ranks'],f['capacities'],rc.increments):
   data=array('Q',values)
   if sys.byteorder!='little':data.byteswap()
   stream.write(data.tobytes())
 for event in cache['events']:
  file=Path(event['path']);assert sha(file)==event['sha256'];bindings[str(file)]=event['sha256'];data=file.read_bytes();assert len(data)==8*len(nodes);d=struct.unpack('<'+str(len(nodes))+'Q',data);assert d[event['sink']]==0;assert cache['cutoff_integer']==rc.scale//(2*10**9) and all(value<=cache['cutoff_integer'] for value in d)
  below_cap+=sum(value<cache['cutoff_integer'] for value in d);total_values+=len(d);arguments.append(str(event['sink'])+':'+str(file))
  certified+=1
 result=subprocess.run([str(binary),str(graphfile),*arguments],capture_output=True,text=True,check=True);proof=json.loads(result.stdout);assert proof['certificates']==certified;bindings[str(graphfile)]=sha(graphfile)
 assert certified<=cache['misses'] and cache['misses']-certified<=cache['aborted'];assert cache['evictions']==max(0,certified-cache['max_entries']);assert cache['retained_distance_bytes']==min(certified,cache['max_entries'])*8*len(nodes)
 rows.append(dict(name=name,publications=certified,misses=cache['misses'],hits=cache['hits'],evictions=cache['evictions'],aborted=cache['aborted'],all_archived_bounds_admissible=True,below_cap_values=below_cap,total_archived_values=total_values,compiled_certificate_proof=proof,model_fingerprint_exact=True,retained_bytes=cache['retained_distance_bytes']));print('PASS cache',name,certified,flush=True)
assert all(sha(path)==h for path,h in bindings.items());(out/'cache_cpp_v3_verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings),indent=2)+'\n')
