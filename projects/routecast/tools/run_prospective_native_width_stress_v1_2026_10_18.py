"""Preserve all fixed native width-stress outcomes, serially and without timeout."""
import json,os,re,shutil,subprocess,time,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 spec=R/'experiments/prospective_native_width_stress_protocol_v1_2026-10-18/protocol.json';p=json.loads(spec.read_text());assert all(sha(k)==h for k,h in p['bindings'].items());root=R/'experiments/prospective_native_width_stress_v1_2026-10-18';root.mkdir();stat=Path('/proc/self/stat').read_text().split(') ',1)[1].split();(root/'live_process.json').write_text(json.dumps(dict(pid=os.getpid(),startticks=stat[19]))+'\n');bindings={**p['bindings'],str(spec):sha(spec),str(Path(__file__).resolve()):sha(Path(__file__).resolve())};rows=[]
 for job in p['jobs']:
  name=f"{job['design']}_width{job['width']}";folder=root/name;folder.mkdir();copytick=time.perf_counter()
  for n in ['design.blif','design.net','design.place']:shutil.copyfile(Path(job['input_directory'])/n,folder/n)
  staging=time.perf_counter()-copytick;graph=folder/'rr_graph.xml';command=job['command_without_RR_output']+['--write_rr_graph',str(graph)];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};(folder/'startup.json').write_text(json.dumps(dict(bindings=bindings,command=command,input_hashes={n:sha(folder/n) for n in ['design.blif','design.net','design.place']}),indent=2)+'\n');print('WIDTH_STRESS_NATIVE_START',name,flush=True);tick=time.perf_counter()
  with (folder/'native.log').open('x') as log:code=subprocess.run(command,cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
  seconds=time.perf_counter()-tick;text=(folder/'native.log').read_text();stats=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',text);status='UNLABELLED_TOOL_OR_INPUT_ERROR'
  if code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text:status='NATIVE_SUCCESS_PENDING_INDEPENDENT_PHYSICAL_CANONICAL'
  elif code==2 and f"Circuit is unroutable with a channel width factor of {job['width']}." in text and 'VPR failed to implement circuit' in text and len(stats)==1 and int(stats[0][1])>0 and int(stats[0][2])>0:status='OBSERVED_NATIVE_ROUTING_FAILURE_UNDER_FIXED100ITER_BUDGET'
  files={str(q):sha(q) for q in [folder/'native.log',folder/'startup.json',graph] if q.exists()};row=dict(name=name,design=job['design'],width=job['width'],status=status,exit_status=code,native_graph_generation_write_route_cleanup_seconds=seconds,input_staging_seconds=staging,router_stats=[list(map(int,x)) for x in stats],RR_graph_written=graph.exists(),files=files,command=command,not_a_proof_of_intrinsic_unroutability=True,strict_unseen_family=False);(folder/'terminal.json').write_text(json.dumps(dict(bindings=bindings,**row),indent=2)+'\n');rows.append(row);(root/'stages.json').write_text(json.dumps(rows,indent=2)+'\n');print('WIDTH_STRESS_NATIVE_DONE',json.dumps({k:v for k,v in row.items() if k not in ['files','command']}),flush=True)
 (root/'results.json').write_text(json.dumps(dict(status='all4_prospective_width_stress_runs_terminal_independent_review_pending',bindings=bindings,cases=rows),indent=2)+'\n')
if __name__=='__main__':main()
