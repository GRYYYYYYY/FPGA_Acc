"""One fixed source-geometry B control against archived source A; no target labels replaced."""
import pathlib,json,hashlib,shutil,subprocess,os,time,resource,re,sys,traceback
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent/'native_resume_prototype'))
from shared_compact_native_inventory_v1 import Inventory
from stream_native_route_audit_expat_v3 import audit
from canonical_reload_pin_index_expat_v3 import canonical_reload,binary as reload_binary,identity
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 O=R/'experiments/mmc_source_geometry_binary_B_control_v1_2026-10-19';O.mkdir(exist_ok=False);A=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/native/mmc';arp=A/'receipt.json';ar=json.loads(arp.read_text());cmd=ar['command'].copy();oldbinary=pathlib.Path(cmd[0]);newbinary=R/'build/native_owner_trace_cold_v1_2026-10-19/sequence_vpr';bp=newbinary.parent/'receipt.json';b=json.loads(bp.read_text());assert b['read_only_hooks_original_routing_source_recovered_exactly'] and b['binary_sha256']==sha(newbinary);cmd[0]=str(newbinary);graph=pathlib.Path(cmd[cmd.index('--read_rr_graph')+1]);assert sha(oldbinary)!=sha(newbinary)
  # Bind frozen old inputs, actual A output, and exact B binary before staging.
 bindings={str(p):sha(p) for p in [arp,bp,oldbinary,newbinary,graph,pathlib.Path(cmd[1]),reload_binary,identity,pathlib.Path(__file__).resolve()]}
 for name in ['design.blif','design.net','design.place','output.route','native.log']:
  p=A/name;assert ar['files'][str(p)]==sha(p);bindings[str(p)]=sha(p)
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};D=O/'native';owner=D/'owner_trace.tsv';env['ROUTECAST_NATIVE_OWNER_TRACE']=str(owner);write(O/'protocol.json',dict(bindings=bindings,reference_A_directory=str(A),reference_A_command=ar['command'],B_command=cmd,environment_set={'ROUTECAST_NATIVE_OWNER_TRACE':str(owner)},replications=1,selection='Exactly source geometry and all original source A command arguments, only executable B and private read-only owner output hook added. All staged input bytes identical.',scope='Cross-binary/observer build control, not pure placement effect or causal identification of a specific hook. No new target layout, revised original labels, weight tuning, performance or generalization claim. Any route difference requires original XML and canonical audit before admission.'))
 assert int(pathlib.Path('/sys/fs/cgroup/memory.max').read_text())-int(pathlib.Path('/sys/fs/cgroup/memory.current').read_text())>=40*2**30;D.mkdir()
 for name in ['design.blif','design.net','design.place']:shutil.copyfile(A/name,D/name);assert sha(D/name)==bindings[str(A/name)]
 def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30))
 print('SOURCE_GEOMETRY_BINARY_B_NATIVE_START',flush=True);t=time.perf_counter()
 with (D/'native.log').open('x') as log:
  child=subprocess.Popen(cmd,cwd=D,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit);write(O/'live_process.json',dict(pid=child.pid,startticks=pathlib.Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],command=cmd));code=child.wait()
 native_seconds=time.perf_counter()-t;text=(D/'native.log').read_text();row=dict(exit_code=code,native_seconds=native_seconds,FULL_pass='Completed routing consistency check successfully.' in text,VPR_success='VPR succeeded' in text,route_bytes_equal_A=(D/'output.route').exists() and sha(D/'output.route')==bindings[str(A/'output.route')]);write(O/'native_terminal.json',row);assert code==0 and row['FULL_pass'] and row['VPR_success'];row['wirelength']=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]);row['CPD_ns']=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1]);print('SOURCE_GEOMETRY_B_NATIVE_TERMINAL',row,flush=True)
 try:
  physical=audit(graph,D/'output.route');assert physical['overflow_units']==0 and physical['routed_nets']==55300 and len(physical['connections'])==115572;write(D/'physical_audit.json',physical);candidate=dict(files={str(p):sha(p) for p in D.iterdir() if p.is_file()},command=cmd,width=128,decision='R',cpd_ns=row['CPD_ns']);print('SOURCE_GEOMETRY_B_CANONICAL_START',flush=True);canonical=canonical_reload(candidate,D,O/'canonical',Inventory(graph));assert canonical['semantic_consistency_gate_pass'];assert all(sha(pathlib.Path(p))==h for p,h in bindings.items());write(O/'receipt.json',dict(status='SAME_SOURCE_GEOMETRY_BINARY_B_FULL_PHYSICAL_CANONICAL_PASS',native=row,canonical=canonical,bindings=bindings,scope='Same geometry, input bytes, original parameters and graph path; binary/observer build changed plus private logging hook. Compare actual A/B physical paths before causal placement claims. No original label or quality-gate changes, no speedup claim.'));print('SOURCE_GEOMETRY_B_CONTROL_COMPLETE',flush=True)
 except Exception as e:write(O/'failure.json',dict(error=repr(e),traceback=traceback.format_exc()));raise
if __name__=='__main__':main()
