"""Fresh native identity-only partition of already exposed development layouts."""
import sys,json,os,shutil,subprocess,resource,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 ep=R/'experiments/prospective_layout_swap_endpoints_v2_2026-10-18/verification.json';p=json.loads(ep.read_text());seed=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc';binary=R/'build/native_ignored_identity_v1_2026-10-08/routecast_net_identity_vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';out=R/'experiments/prospective_layout_swap_native_partition_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={str(x):sha(x) for x in [Path(__file__),ep,binary,arch,seed/'design.blif',seed/'design.net']};rows=[]
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Three native identity-only invocations, no RR construction/routing/quality target. Native expected exit1 is admitted only with explicit identity phase rr_graph_skipped. Fresh ignored flags from each layout, no transfer from source counts.',workers=1,AS_limit_bytes=8*2**30,elapsed_timeout=None),indent=2))
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 for e in p['episodes']:
  d=out/f'episode_{e["episode"]:02}';d.mkdir();raw=json.loads(Path(e['endpoints']).read_text());assert sha(e['endpoints'])==e['endpoints_sha256'];assert sha(e['placement'])==e['placement_sha256']
  for name in ['design.blif','design.net']:shutil.copyfile(seed/name,d/name)
  shutil.copyfile(e['placement'],d/'design.place');table=d/'identity.jsonl';cmd=[str(binary),str(arch),'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','missing.route','--route_chan_width','128','--num_workers','1','--seed','1','--check_route','full'];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_IDENTITY_ONLY='1',ROUTECAST_NET_IDENTITY_FILE=str(table));start=time.perf_counter()
  with (d/'identity.log').open('x') as log:
   child=subprocess.Popen(cmd,cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits);(d/'live_process.json').write_text(json.dumps(dict(pid=child.pid,command=cmd)));print('IDENTITY CHILD',e['episode'],child.pid,flush=True);code=child.wait()
  phase=Path(str(table)+'.phase.json');assert code==1 and json.loads(phase.read_text())['rr_graph_skipped'];records=[json.loads(line) for line in table.read_text().splitlines()];native={r['name']:r for r in records};assert len(native)==len(records)
  physical=[];ignored=[];translation=[]
  for q in raw['connections']:
   name=raw['net_names'][str(q['net_id'])];assert name in native
   if native[name]['ignored']:ignored.append(q['connection_id'])
   else:translation.append(q['connection_id']);physical.append(dict(q,connection_id=len(physical)))
  assert len(physical)+len(ignored)==len(raw['connections']);assert not list(d.glob('*.route'))
  result=dict(raw,connections=physical,native_demand_policy='exclude_authenticated_native_ignored_NETs_v1',original_connection_count=len(raw['connections']),native_ignored_connection_count=len(ignored));result['inputs']=dict(raw['inputs'],native_identity=dict(path=str(table),sha256=sha(table)),all_endpoints=dict(path=e['endpoints'],sha256=e['endpoints_sha256']));(d/'endpoints.json').write_text(json.dumps(result,separators=(',',':')));(d/'partition.json').write_text(json.dumps(dict(physical_to_original_connection_ids=translation,ignored_original_connection_ids=ignored)));rows.append(dict(episode=e['episode'],exit_code=code,rr_graph_skipped=True,raw_connections=len(raw['connections']),physical_connections=len(physical),ignored_connections=len(ignored),component_seconds=time.perf_counter()-start,files={str(f):sha(f) for f in d.iterdir() if f.is_file()}));print('IDENTITY PARTITION DONE',e['episode'],len(physical),len(ignored),flush=True)
 for path,h in bindings.items():assert sha(path)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='fresh_native_identity_partitions_captured_all_three_development_layouts',bindings=bindings,episodes=rows,scope='Fresh native ignored flags and original-to-physical connection translation only. Does not certify every native pin identity, native RR placement consistency, route legality, predictive quality or net-time benefit. No candidate family labels or new routes.'),f,indent=2)
if __name__=='__main__':main()
