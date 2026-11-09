"""Verify actual CU traces and immutable artifacts for the serialized fixture."""
from pathlib import Path
import argparse,json,hashlib,re,time,subprocess
p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('build',type=Path);p.add_argument('--handoff',action='store_true');a=p.parse_args();out=a.run;build=a.build
manifest=json.loads((out/'manifest.json').read_text());assert manifest['returncode']==0
r=json.loads((out/'result.json').read_text());expected_counts=(3,5,13) if a.handoff else (2,3,7);assert r['status']=='passed' and tuple(r[k] for k in ['owner_calls','binding_calls','worker_calls'])==expected_counts
assert r['authority_reuploads_after_initialization']==0
assert (r['final_cost'],r['observations'])==((28,3) if a.handoff else (20,2))
if a.handoff:assert r['session_handoff_verified']
log=(out/'run.log').read_text();worker=[tuple(map(int,x)) for x in re.findall(r'XRT worker call=(\d+) op=(\d+) queued=(\d+) observations=(\d+) status=(\d+)',log)]
expected_worker=[(1,4,1,0,0),(2,2,0,0,0),(3,1,1,1,0),(4,1,2,2,0),(5,2,1,2,0),(6,2,0,2,1),(7,3,0,2,0)]
if a.handoff:expected_worker += [(8,4,1,2,0),(9,2,0,2,0),(10,1,0,2,1),(11,1,1,3,0),(12,2,0,3,0),(13,3,0,3,0)]
assert worker==expected_worker
binding=[tuple(map(int,x)) for x in re.findall(r'XRT binding call=(\d+) kind=(\d+) status=(\d+)',log)];expected_binding=[(1,1,0),(2,1,1),(3,2,0)]
if a.handoff:expected_binding += [(4,1,1),(5,1,0)]
assert binding==expected_binding
owner=[tuple(map(int,x)) for x in re.findall(r'XRT owner call=(\d+) commands=(\d+) updates=(\d+) error=(\d+)',log)];assert owner==([(1,2,0,0),(2,1,1,0),(3,2,0,0)] if a.handoff else [(1,2,0,0),(2,1,1,0)])
inputs=json.loads((out/'inputs.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
image_hash=hashlib.sha256((build/'joint.xclbin').read_bytes()).hexdigest();metadata=json.loads((build/'xclbin_metadata_audit.json').read_text());assert image_hash==manifest['xclbin_sha256']==metadata['xclbin_sha256'] and metadata['status']=='passed'
nm=subprocess.run(['nm','-C',str(out/'host')],capture_output=True,text=True,check=True).stdout;assert not re.search(r'^\w+ [TtWw] dieroute_(owner_publish|native_search_worker|native_search_owner_envelope)_hbm\b',nm,re.M)
raw=(out/'stdout.log').read_text();assert 'All the simulator processes exited successfully' in raw
paths=[out/'result.json',out/'run.log',out/'stdout.log',out/'host',out/'inputs.json',build/'xclbin_metadata_audit.json']
report={'status':'passed','verified_ns':time.time_ns(),'actual_cu_calls':sum(expected_counts),'xclbin_sha256':image_hash,'session_handoff':a.handoff,'cpu_kernel_symbols_absent':True,'result':r,'evidence_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'scope':'Serialized shared-BO joint hw_emu fixture; no native-route, autonomous async protocol, full-capacity RTL or board proof','board_result':False,'research_complete':False};(out/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','actual_cu_calls':sum(expected_counts),'session_handoff':a.handoff}))
