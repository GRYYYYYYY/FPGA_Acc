"""Fresh native typed timing graphs and complete clock-constraint snapshots."""
import hashlib,json,os,resource,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'experiments/wbuart_nominal_contexts_v1_2026-10-20';T=R/'experiments/wbuart_frame_timings_v1_2026-10-20';S=R/'experiments/wbuart_development_place_v1_2026-10-20';B=R/'build/native_external_clock_constraints_v1_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);old=R/'experiments/prospective_external_family_clock_constraints_v1_2026-10-19/verification.json';cert=json.loads(old.read_text());binary=B/'sequence_vpr';assert sha(binary)==cert['bindings'][str(binary)]
 bp=json.loads((B/'protocol.json').read_text())
 for n,h in bp['bindings'].items():assert sha(Path(n))==h
 tp=T/'verification.json';timing=json.loads(tp.read_text());assert len(timing['rows'])==12
 for n,h in timing['bindings'].items():assert sha(Path(n))==h
 jobs=[]
 for row in timing['rows']:
  previous=Path(row['timing_directory']);proto=json.loads((previous/'protocol.json').read_text());cmd=proto['command'].copy();cmd[0]=str(binary);jobs.append({'case':row['case'],'previous_timing_directory':str(previous),'endpoint':row['endpoint'],'command':cmd})
 bindings={str(p):sha(p) for p in [Path(__file__),old,B/'protocol.json',binary,tp,S/'design.blif']};(O/'protocol.json').write_text(json.dumps({'bindings':bindings,'jobs':jobs,'role':'All12 fresh native timing/clock captures, own current graph/place/netlist. Exit before routing search. Previously built observer reused only as code, no captured old-family values. Float32 graph delays, setup/hold, atom pin metadata, ranges and every native clock query exported. No target routed labels, no fixed offset or dynamic model claim yet.'},indent=2)+'\n');rows=[]
 for job in jobs:
  d=O/job['case'];d.mkdir(parents=True);e=json.loads(Path(job['endpoint']).read_text());pre={str(Path(job['endpoint'])):sha(Path(job['endpoint']))}
  for src,name in [(Path(e['inputs']['net']['path']),'design.net'),(Path(e['inputs']['place']['path']),'design.place'),(S/'design.blif','design.blif')]:shutil.copyfile(src,d/name);assert sha(src)==sha(d/name);pre.update({str(p):sha(p) for p in [src,d/name]})
  (d/'protocol.json').write_text(json.dumps({'command':job['command'],'endpoint':job['endpoint'],'previous_timing_directory':job['previous_timing_directory'],'bindings':pre,'marker':'RC_TIMING_GRAPH_SNAPSHOT_EXIT_BEFORE_ROUTING'},indent=2)+'\n');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};start=time.perf_counter()
  def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  with (d/'native.log').open('x') as f:
   child=subprocess.Popen(job['command'],cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit);st=Path(f'/proc/{child.pid}/stat').read_text().rsplit(') ',1)[1].split();(O/'live_process.json').write_text(json.dumps({'case':job['case'],'pid':child.pid,'start_ticks':st[19]},indent=2)+'\n');rc=child.wait()
  for n,h in pre.items():assert sha(Path(n))==h
  required=['timing_nodes.tsv','timing_edges.tsv','timing_atoms.tsv','clock_constraints.tsv','initial_connections.tsv'];passed=rc==0 and 'RC_TIMING_GRAPH_SNAPSHOT_EXIT_BEFORE_ROUTING' in (d/'native.log').read_text() and not list(d.glob('*.route')) and all((d/n).exists() for n in required)
  receipt={'exit_status':rc,'capture_passed':passed,'seconds':time.perf_counter()-start,'new_target_route_labels':False,'bindings':{str(p):sha(p) for p in [d/'protocol.json',d/'native.log',*[d/n for n in required if (d/n).exists()]]}};(d/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');rows.append({'case':job['case'],'directory':str(d),'passed':passed,'receipt_sha256':sha(d/'receipt.json')});(O/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print('WBUART_NOMINAL_CAPTURE',job['case'],passed,flush=True)
  assert passed
 for n,h in bindings.items():assert sha(Path(n))==h
 (O/'terminal.json').write_text(json.dumps({'status':'ALL12_NATIVE_NOMINAL_CONTEXT_CAPTURES_TERMINAL','rows':rows,'bindings':{str(O/'protocol.json'):sha(O/'protocol.json')},'independent_graph_constraints_and_CID_audit_pending':True,'new_target_route_labels':False,'strict_unseen_admitted':False},indent=2)+'\n')
if __name__=='__main__':main()
