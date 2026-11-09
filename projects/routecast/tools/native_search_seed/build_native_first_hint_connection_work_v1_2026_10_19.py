"""Private header overlay, reversible actual sink-operation hooks, original policy."""
import sys,json,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 B=R/'build/native_first_iteration_hint_v1_2026-10-19';C=R/'build/native_owner_trace_cold_v1_2026-10-19';bp=B/'receipt.json';b=json.loads(bp.read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'];P=json.loads((B/'protocol.json').read_text());D=R/'build/native_first_hint_connection_work_v1_2026-10-19';D.mkdir(exist_ok=False);src=D/'source';src.mkdir();overlay=src/'overlay';overlay.mkdir();templates=R/'tools/native_search_seed/connection_work_trace_v1_2026_10_18';vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route';bindings={**b['bindings'],str(bp):sha(bp),str(B/'protocol.json'):sha(B/'protocol.json'),**closure([Path(__file__)])}
 for p in vendor.iterdir():
  if p.suffix in ['.h','.tpp']:shutil.copyfile(p,overlay/p.name);bindings[str(p)]=sha(p)
 for name in ['route.cpp','route_net.cpp','routecast_owner_trace.h','routecast_owner_trace_impl.h']:
  origin=(C if name=='route_net.cpp' else B)/'source'/name;shutil.copyfile(origin,src/name);bindings[str(origin)]=sha(origin)
 for hp in (B/'source').glob('*.h'):
  if not (src/hp.name).exists():shutil.copyfile(hp,src/hp.name)
 for name in ['connection_trace.h','connection_trace_impl.h']:shutil.copyfile(templates/name,src/name);bindings[str(templates/name)]=sha(templates/name)
 hp=src/'routecast_owner_trace.h';oldheader=hp.read_text();hp.write_text(oldheader+'\n#include "connection_trace.h"\n')
 implp=src/'routecast_owner_trace_impl.h';original=implp.read_text();text=original;edits=[]
 def edit(a,z):
  nonlocal text
  assert text.count(a)==1,a;text=text.replace(a,z);edits.append((a,z))
 edit('rc_trace_checkpoint("initial",nets);','routecast_connection_trace_begin(nets);rc_trace_checkpoint("initial",nets);')
 edit('rc_trace_iter=itry;rc_trace_checkpoint("iteration_begin",nets);','rc_trace_iter=itry;routecast_connection_iter_begin(itry);rc_trace_checkpoint("iteration_begin",nets);')
 edit('    std::fprintf(rc_trace_file,"S %d %zu %zu %zu %zu\\n",itry,stats.nets_routed,stats.connections_routed,stats.heap_pushes,stats.heap_pops);','    routecast_connection_iter_end(itry,stats);\n    std::fprintf(rc_trace_file,"S %d %zu %zu %zu %zu\\n",itry,stats.nets_routed,stats.connections_routed,stats.heap_pushes,stats.heap_pops);')
 edit('    FILE* closed=rc_trace_file;','    routecast_connection_trace_finish(success);\n    FILE* closed=rc_trace_file;')
 restored=text
 for a,z in reversed(edits):restored=restored.replace(z,a,1)
 assert restored==original;implp.write_text(text+'\n#include "connection_trace_impl.h"\n')
 tpp=overlay/'route_net.tpp';original_tpp=tpp.read_text();text=original_tpp;tpp_edits=[]
 def te(a,z):
  nonlocal text
  assert text.count(a)==1,a;text=text.replace(a,z);tpp_edits.append((a,z))
 te('        ++router_stats.connections_routed;','        ++router_stats.connections_routed;\n        routecast_connection_success(net_id,target_pin,router_stats);')
 te('    RRNodeId sink_node = route_ctx.net_rr_terminals[net_id][target_pin];','    RRNodeId sink_node = route_ctx.net_rr_terminals[net_id][target_pin];\n    routecast_connection_attempt(net_id,target_pin,router_stats);')
 start=text.index('inline NetResultFlags route_sink(');prefix=text[:start];sub=text[start:];anchor='        flags.success = false;\n        router.reset_path_costs();\n        return flags;';assert sub.count(anchor)==1;replacement='        flags.success = false;\n        router.reset_path_costs();\n        routecast_connection_failure(net_id,target_pin,router_stats);\n        return flags;';sub=sub.replace(anchor,replacement);text=prefix+sub;tpp_edits.append((anchor,replacement));restored=text
 for a,z in reversed(tpp_edits):restored=restored.replace(z,a,1)
 assert restored==original_tpp;tpp.write_text('#include "routecast_owner_trace.h"\n'+text)
 for name in ['route.cpp','route_net.cpp']:assert (src/name).read_bytes()==((C if name=='route_net.cpp' else B)/'source'/name).read_bytes()
 for p in src.rglob('*'):
  if p.is_file():bindings[str(p)]=sha(p)
 compiles=[]
 for old,name,obj in zip([P['compile'],json.loads((C/'protocol.json').read_text())['compile'][1]],['route.cpp','route_net.cpp'],['route.o','route_net.o']):compiles.append([old[0],'-I'+str(overlay),'-I'+str(src),*old[1:-4],'-c',str(src/name),'-o',str(D/obj)])
 link=[str(D/'route_net.o') if x==str(C/'route_net.o') else x.replace(str(B)+'/',str(D)+'/') for x in P['link']];assert str(D/'route.o') in link and str(D/'route_net.o') in link;protocol=dict(bindings=bindings,compile=compiles,link=link,impl_edits=edits,template_edits=tpp_edits,observer_hooks_reversible_to_unchanged_base_and_vendor_template=True,scope='Reuse of existing connection work observer on exact first-hint base; private copied headers and opt-in read-only connection observer. Hook attempts/failures in native route_sink, successes exactly at native connections_routed increment. Initial native pin terminals/reach flags and NET-name hex table included; actual RouterStats heap snapshots surround each sink attempt, with attributed and residual iteration work explicit. Runtime policy/artifact equivalence, completeness and manifest CID mapping all pending; not an RRR result yet.')
 (D/'protocol.json').write_text(json.dumps(protocol,indent=2))
 with Cache().installed():
  assert all(sha(p)==h for p,h in bindings.items())
  for i,cmd in enumerate(compiles):
   print('CONNECTION OBSERVER COMPILE',i,flush=True)
   with (D/f'compile_{i}.log').open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
  print('CONNECTION OBSERVER LINK',flush=True)
  with (D/'link.log').open('x') as log:subprocess.run(link,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (D/'receipt.json').open('x') as f:json.dump(dict(status='connection_work_observer_build_pass_runtime_and_mapping_pending',bindings={**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},binary_sha256=sha(D/'sequence_vpr'),runtime_equivalence_pending=True,distinct_CID_RRR_certified=False),f,indent=2)
 print('CONNECTION OBSERVER BUILD PASS',flush=True)
if __name__=='__main__':main()
