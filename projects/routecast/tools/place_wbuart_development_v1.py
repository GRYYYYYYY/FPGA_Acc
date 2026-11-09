"""Frozen one-shot development placement input; no family/test/route admission."""
import datetime,hashlib,json,os,resource,shutil,signal,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/wbuart_pack_v1_2026-10-20';O=R/'experiments/wbuart_development_place_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):
 with (O/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False)
 proofpaths=[R/'experiments/wbuart_equivalence_keepdc_coverage_v1_2026-10-20/verification.json',R/'experiments/wbuart_packed_FF_v2_2026-10-20/verification.json',R/'experiments/wbuart_native_packed_cut_v1_2026-10-20/independent_verification_v1.json'];proofs=[json.loads(p.read_text()) for p in proofpaths];assert proofs[0]['gate_state_bits']==599 and proofs[0]['matched_state_initial_constraints_equal'] and proofs[1]['FF_bits']==599 and proofs[2]['FF_state_pairs']==599
 for d in proofs:
  for n,h in d['bindings'].items():assert sha(Path(n))==h
 packprotocol=json.loads((P/'protocol.json').read_text());vpr=Path(packprotocol['command'][0]);arch=Path(packprotocol['command'][1]);root=ET.parse(P/'design.net').getroot();assert root.get('architecture_id')=='SHA256:'+sha(arch) and root.get('atom_netlist_id')=='SHA256:'+sha(P/'design.blif')
 for n in ['design.blif','design.net']:shutil.copyfile(P/n,O/n);assert sha(P/n)==sha(O/n)
 cmd=[str(vpr),str(arch),'design.blif','--place','--net_file','design.net','--place_file','source.place','--place_algorithm','criticality_timing','--timing_analysis','on','--place_chan_width','128','--route_chan_width','128','--num_workers','1','--seed','1']
 bindings={str(p):sha(p) for p in [Path(__file__),*proofpaths,vpr,arch,P/'design.blif',P/'design.net',O/'design.blif',O/'design.net']}
 save('protocol.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'bindings':bindings,'timeout_seconds':300,'AS_limit_bytes':8*2**30,'role':'Development input preparation only; no strict unseen assignment or validation cohort. One seed1,width128,worker1 placement; no new pack/route, no label-dependent choice. Retain failure/timeout.','source_scope':'Unchanged default RTL compiled with keepdc; all599 state init constraints retained,602 Yosys-defined equivalence properties. Native loaded LUT cut matches only under explicit-zero unused physical inputs. No default-X wholeHDL/four-state or physical timing proof.','preserved':'Original cohort/metrics/labels/gates/budgets/unavailable cases/negative outcomes unchanged. Family exposure scan still pending.','cost_scope':'Prep/proofs/staging/placement remain upstream paid costs in any later full-flow comparison; no gain claim.'})
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};timeout=False;start=time.perf_counter()
 def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 with (O/'place.log').open('x') as f:
  child=subprocess.Popen(cmd,cwd=O,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit,start_new_session=True);st=Path(f'/proc/{child.pid}/stat').read_text().rsplit(') ',1)[1].split();save('live_process.json',{'pid':child.pid,'start_ticks':st[19],'command':cmd});print('WBUART_PLACE_CHILD',child.pid,flush=True)
  try:rc=child.wait(timeout=300)
  except subprocess.TimeoutExpired:timeout=True;os.killpg(child.pid,signal.SIGTERM);rc=child.wait()
 for n,h in bindings.items():assert sha(Path(n))==h
 assert not list(O.glob('*.route'));rows=[]
 if (O/'source.place').exists():
  for s in (O/'source.place').read_text().splitlines():
   t=s.split()
   if len(t)>=5 and not t[0].startswith('#') and all(x.lstrip('-').isdigit() for x in t[1:4]):rows.append(t)
 passed=rc==0 and bool(rows) and 'VPR succeeded' in (O/'place.log').read_text();save('receipt.json',{'status':'DEVELOPMENT_PLACEMENT_COMPLETE_PENDING_INDEPENDENT_AUDIT' if passed else 'DEVELOPMENT_PLACEMENT_FAILED_RETAINED','exit_status':rc,'timeout':timeout,'seconds':time.perf_counter()-start,'placement_rows':len(rows),'strict_unseen_admitted':False,'new_route_labels':False,'bindings':{str(p):sha(p) for p in O.iterdir() if p.is_file()}});print('WBUART_PLACE_TERMINAL',rc,passed,len(rows),flush=True)
if __name__=='__main__':main()
