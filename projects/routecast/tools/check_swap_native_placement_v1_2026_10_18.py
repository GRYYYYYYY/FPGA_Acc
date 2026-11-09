"""Native placement/RR consistency only; missing route is deliberate terminal boundary."""
import sys,json,os,shutil,subprocess,resource,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 proof=R/'experiments/prospective_layout_swap_native_pin_identity_v1_2026-10-18/verification.json';v=json.loads(proof.read_text());assert len(v['episodes'])==3
 for p,h in v['bindings'].items():assert sha(p)==h
 source=R/'experiments/prospective_layout_swap_native_partition_v1_2026-10-18';graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';binary=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';out=R/'experiments/prospective_layout_swap_native_placement_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [Path(__file__),proof,graph,binary,arch]};rows=[]
 commands=[]
 for e in v['episodes']:
  d=out/f'episode_{e["episode"]:02}';d.mkdir();src=source/d.name
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(src/name,d/name);bindings[str(src/name)]=sha(src/name)
  commands.append([str(binary),str(arch),'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','missing.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--check_route','full'])
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,AS_limit_bytes=8*2**30,timeout_seconds=None,scope='Native placement consistency with exact old MMC RR graph; deliberate missing.route boundary. No routing invoked, labels or timing utility claims.'),indent=2))
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 for e,cmd in zip(v['episodes'],commands):
  d=out/f'episode_{e["episode"]:02}';tick=time.perf_counter();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
  with (d/'check.log').open('x') as log:
   child=subprocess.Popen(cmd,cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits);(d/'live_process.json').write_text(json.dumps(dict(pid=child.pid)));print('NATIVE PLACEMENT CHILD',e['episode'],child.pid,flush=True);code=child.wait()
  text=(d/'check.log').read_text();passed=code==1 and 'Completed placement consistency check successfully.' in text and 'Cannot open missing.route' in text and not list(d.glob('*.route'));rows.append(dict(episode=e['episode'],exit_code=code,placement_consistency_pass=passed,component_seconds=time.perf_counter()-tick,files={str(p):sha(p) for p in d.iterdir() if p.is_file()}));print('NATIVE PLACEMENT RESULT',e['episode'],code,passed,flush=True)
  if not passed:break
 for p,h in bindings.items():assert sha(p)==h
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='all_three_native_placement_consistency_pass' if len(rows)==3 and all(e['placement_consistency_pass'] for e in rows) else 'native_placement_consistency_not_admitted',bindings=bindings,episodes=rows,new_routes=False,scope='Native input placement consistency only; expected missing-route failure is not routing success, no quality/utility/timing or heldout admission.'),f,indent=2)
if __name__=='__main__':main()
