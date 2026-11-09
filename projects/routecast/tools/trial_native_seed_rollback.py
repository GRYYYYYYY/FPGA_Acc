import json,shutil,subprocess,os,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_seed_rollback_v2_2026-10-06';work=root/'work/native_seed_rollback_v2_2026-10-06';out.mkdir();work.mkdir();results=[]
for kind,parent in [('complete','native_search_seed_v3_2026-10-06'),('moved','native_move_seed_v5_2026-10-06')]:
 meta=json.loads((root/'experiments'/parent/'command.json').read_text());src=Path(meta['cwd']);cwd=work/kind;cwd.mkdir();case=out/kind;case.mkdir()
 for name in ('design.blif','design.net','design.place','seed.route'):shutil.copyfile(src/name,cwd/name)
 seed=(cwd/'seed.route').read_text();bad=re.sub(r'Net_pin_index:\s*\d+','Net_pin_index: 999999',seed,count=1);assert bad!=seed;(cwd/'bad.route').write_text(bad);cmd=meta['command'].copy();cmd[0]=str(root/'build/native_seed_rollback_v2_2026-10-06/routecast_search_seed_vpr');env=os.environ.copy();env['ROUTECAST_NATIVE_SEED']=str(cwd/'seed.route');env['ROUTECAST_BAD_IMPORT']=str(cwd/'bad.route')
 with (case/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 assert code==0,(kind,code);assert sha(cwd/'before_bad.route')==sha(cwd/'after_bad.route');assert sha(cwd/'before_bad.nodes')==sha(cwd/'after_bad.nodes');assert 'snapshot restored' in (case/'run.log').read_text();graph=cmd[cmd.index('--read_rr_graph')+1];a=audit(graph,cwd/'output.route');assert len(a['connections'])==129 and a['overflow_units']==0;(case/'physical_audit.json').write_text(json.dumps(a,indent=2)+'\n');baseline=sha(src/'output.route');assert sha(cwd/'output.route')==baseline
 results.append({'case':kind,'exit_code':code,'before_after_trace_sha256':sha(cwd/'before_bad.route'),'before_after_node_state_sha256':sha(cwd/'before_bad.nodes'),'final_route_sha256':baseline,'final_matches_no_fault_control':True,'log_sha256':sha(case/'run.log'),'command':cmd,'seed_sha256':sha(cwd/'seed.route'),'bad_seed_sha256':sha(cwd/'bad.route')});print(kind,'rollback and final parity passed',flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'scope':'Same-process fixed graph/netlist/placement import failure restores 14 saved routing fields by swap; traces/node costs and final search parity observed. Not whole placement/packing/STA move transaction, not leak-freedom or concurrent atomicity proof.'},indent=2)+'\n')
