"""Twelve fresh current-native timing snapshots, no route search or timing reuse."""
import datetime,hashlib,json,os,resource,shutil,subprocess,time
from pathlib import Path
from verify_wbuart_frame_initial_timing_v1 import verify
from load_wbuart_current_initial_timing_v1 import load,epoch
R=Path(__file__).resolve().parents[1];O=R/'experiments/wbuart_frame_timings_v1_2026-10-20';F=R/'experiments/wbuart_width_frames_v2_2026-10-20';S=R/'experiments/wbuart_development_place_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False);matrix=json.loads((F/'verification.json').read_text());assert len(matrix['rows'])==12
 for n,h in matrix['bindings'].items():assert sha(Path(n))==h
 build=R/'build/native_initial_timing_pin_snapshot_v3_2026-10-19';br=json.loads((build/'receipt.json').read_text());binary=build/'sequence_vpr';assert sha(binary)==br['binary_sha256']
 for d in [br,json.loads((build/'protocol.json').read_text())]:
  for n,h in d['bindings'].items():assert sha(Path(n))==h
 old=R/'experiments/prospective_external_family_current_initial_timing_v1_2026-10-19/protocol.json';template=json.loads(old.read_text())['command'];jobs=[]
 for row in matrix['rows']:
  fp=Path(row['verification']);frame=json.loads(fp.read_text());ep=fp.parent/'routing_endpoints.json';e=json.loads(ep.read_text());case=f"w{frame['width']:03d}/{frame['frame']}";cmd=template.copy();cmd[0]=str(binary);cmd[cmd.index('--read_rr_graph')+1]=e['inputs']['graph']['path'];cmd[cmd.index('--route_chan_width')+1]=str(frame['width']);cmd[cmd.index('--max_router_iterations')+1]='300';jobs.append({'case':case,'frame_proof':str(fp),'endpoint':str(ep),'command':cmd})
 bindings={str(p):sha(p) for p in [Path(__file__),F/'verification.json',F/'independent_verification_v1.json',build/'receipt.json',build/'protocol.json',binary,old,R/'tools/verify_wbuart_frame_initial_timing_v1.py',R/'tools/load_wbuart_current_initial_timing_v1.py',S/'design.blif']}
 save(O/'protocol.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'jobs':jobs,'bindings':bindings,'expected_all_sink_pins':2566,'expected_routing_data_CIDs':2493,'ignored_clock_pins':71,'ignored_nonclock_pins':2,'policy':'All12 fresh native initial snapshots, actual current graph/place/netlist per frame. REAL getter plus atom/pin bits; exit before first getter returns. No source-to-target or cross-width timing reuse, no routing search/default fallback. Every native sink and every declared atom row checked; atom aggregate cardinalities and log total crosschecked, no source-design hardcoded atom count. Full CID provenance retained.'})
 rows=[]
 for job in jobs:
  d=O/job['case'];d.mkdir(parents=True);work=d/'work';work.mkdir();fp=Path(job['frame_proof']);frame=json.loads(fp.read_text());ep=Path(job['endpoint']);e=json.loads(ep.read_text());pre={str(p):sha(p) for p in [fp,ep,Path(e['inputs']['graph']['path']),binary]}
  for src,name in [(Path(e['inputs']['net']['path']),'design.net'),(Path(e['inputs']['place']['path']),'design.place'),(S/'design.blif','design.blif')]:shutil.copyfile(src,work/name);assert sha(src)==sha(work/name);pre.update({str(p):sha(p) for p in [src,work/name]})
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};sets={k:str(work/name) for k,name in [('ROUTECAST_INITIAL_CRITICALITY','criticality.tsv'),('ROUTECAST_INITIAL_TIMING','timing.tsv'),('ROUTECAST_INITIAL_PIN_MANIFEST','pin_manifest.tsv')]};env.update(sets);save(d/'protocol.json',{'command':job['command'],'frame_verification':str(fp),'bindings':pre,'environment_set':sets,'scope':'Initialized current timing only; no search, no native target labels, no STA/physical timing closure or strict unseen certificate.'});start=time.perf_counter()
  def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  with (work/'native.log').open('x') as f:
   child=subprocess.Popen(job['command'],cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit);st=Path(f'/proc/{child.pid}/stat').read_text().rsplit(') ',1)[1].split();(O/'live_process.json').write_text(json.dumps({'case':job['case'],'pid':child.pid,'start_ticks':st[19]},indent=2)+'\n');rc=child.wait()
  text=(work/'native.log').read_text();passed=rc==0 and 'ROUTECAST INITIAL TIMING SNAPSHOT 2566 ' in text and 'ROUTECAST INITIAL PIN MANIFEST 2566 exit_before_first_getter_returns=1' in text and not list(work.glob('*.route'));save(d/'receipt.json',{'capture_passed':passed,'exit_code':rc,'process_seconds':time.perf_counter()-start,'new_route_labels':False,'bindings':{str(p):sha(p) for p in [d/'protocol.json',work/'native.log',*[work/n for n in ['criticality.tsv','timing.tsv','pin_manifest.tsv'] if (work/n).exists()]]}});assert passed
  for n,h in pre.items():assert sha(Path(n))==h
  verify(d,fp);values=load(d,ep);assert len(values)==2493;vp=d/'verification.json';rows.append({'case':job['case'],'endpoint':str(ep),'timing_directory':str(d),'timing_verification':str(vp),'sha256':sha(vp),'connections':len(values),'timing_epoch_sha256':epoch(d)});(O/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print('WBUART_CURRENT_TIMING_VERIFIED',job['case'],len(values),flush=True)
 assert len(rows)==12 and len({r['timing_epoch_sha256'] for r in rows})==12
 for n,h in bindings.items():assert sha(Path(n))==h
 save(O/'verification.json',{'status':'ALL12_CURRENT_WBUART_TIMING_PIN_ATOM_FLOAT32_AND_CID_DOMAINS_VERIFIED','rows':rows,'bindings':{str(O/'protocol.json'):sha(O/'protocol.json'),**{r['timing_verification']:r['sha256'] for r in rows}},'fresh_captures':12,'reused_timing_captures':0,'new_target_route_labels':False,'strict_unseen_admitted':False,'scope':'Current initialized native timing metadata, not current routed STA or final native timing/QoR; no whole-flow gain.'})
if __name__=='__main__':main()
