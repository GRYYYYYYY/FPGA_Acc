"""Fault-only private wrapper: reject stale ticket before a duplicate sync."""
import json,os,shutil,subprocess
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];build=root/'build/native_scoped_sync_faults_2026-10-06';build.mkdir(exist_ok=True);out=root/'experiments/native_scoped_sync_faults_2026-10-06';out.mkdir(exist_ok=True);work=root/'work/native_scoped_sync_faults_2026-10-06';work.mkdir(exist_ok=True)
base=root/'build/native_candidate_move_accept_scoped_2026-10-06';protocol=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());shared={p:sha(p) for p in protocol['inputs_sha256']}
src=(base/'source/sync_once.cpp').read_text();needle=' if(ticket){';assert src.count(needle)==1
src=src.replace(needle,needle+'''\n  const char* fault=std::getenv("ROUTECAST_SYNC_TICKET_FAULT");
  if(fault && std::string(fault)=="placement")const_cast<PlacementContext&>(placement).placement_id+="invalidated";
  if(fault && std::string(fault)=="owner")ticket->nets=nullptr;
  if(fault && std::string(fault)=="epoch")++sync_epoch;
''');src='#include "vpr_error.h"\n'+src;src=src.replace('throw std::runtime_error("candidate sync ticket owner/state mismatch")','vpr_throw(VPR_ERROR_ROUTE,__FILE__,__LINE__,"candidate sync ticket owner/state mismatch")')
(build/'sync_fault.cpp').write_text(src)
obj=build/'sync_fault.o';compile_cmd=[*protocol['compile'][:-4],'-c',str(build/'sync_fault.cpp'),'-o',str(obj)]
with (build/'compile.log').open('w') as f:subprocess.run(compile_cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
link=[str(base/'libvpr.a') if p.endswith('/libvpr.a') else str(build/'fault_vpr') if p.endswith('/routecast_seed_vpr') else p for p in protocol['link']];link=[p for p in link if not p.endswith('/hook.o') and not p.startswith('-Wl,--wrap=')];link[1:1]=[str(base/(n+'.o')) for n in ('read_route','old_traceback','route')]+[str(obj),'-Wl,--wrap=_Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb']
with (build/'link.log').open('w') as f:subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
parent=root/'experiments/native_scoped_sync_next_move_2026-10-06/accept_next';command=json.loads((parent/'command.json').read_text());source=Path(command['cwd']);cmd=command['command'];cmd[0]=str(build/'fault_vpr');results=[]
for fault in ('placement','owner','epoch'):
 cwd=work/fault;cwd.mkdir();case=out/fault;case.mkdir()
 for name in ('design.blif','design.net','design.place','seed.route'):shutil.copyfile(source/name,cwd/name)
 inputs={str(p):sha(p) for p in cwd.iterdir()};env=os.environ.copy();env.update(ROUTECAST_NATIVE_SEED=str(cwd/'seed.route'),ROUTECAST_TIMING_RESTORE_PROBE='1',ROUTECAST_ACCEPT_CANDIDATE='1',ROUTECAST_SYNC_TICKET_FAULT=fault)
 with (case/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 log=(case/'run.log').read_text();assert code==1 and 'candidate sync ticket owner/state mismatch' in log and 'consume context-bound' not in log;assert all(sha(p)==h for p,h in inputs.items());results.append({'fault':fault,'exit_code':code,'inputs_sha256':inputs,'log_sha256':sha(case/'run.log'),'output_route_exists':(cwd/'output.route').exists()});print(fault,code,flush=True)
assert all(sha(p)==h for p,h in shared.items())
(out/'receipt.json').write_text(json.dumps({'results':results,'binary_sha256':sha(cmd[0]),'source_sha256':sha(build/'sync_fault.cpp'),'command':cmd,'shared_inputs_sha256':shared,'scope':'Private fault fixture changes placement identity, ticket owner or ticket epoch after arming. Fails before duplicate sync. This does not establish recovery after acceptance, all packing mutation detection, or concurrency.'},indent=2)+'\n')
