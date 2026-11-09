"""Frozen two-update lifecycle with one live search context and fresh native tails."""
import json,os,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from accepted_route_state import AcceptedRouteState
from staged_placement_reroute import stage_reroute_with_repair
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_sequential_cached4v2_2026-10-06';out.mkdir();work=root/'work/tseng_sequential_cached4v2_2026-10-06';work.mkdir()
original=root/'experiments/nonzero_rc_tseng_endpoints_2026-10-06';swapped=root/'experiments/tseng_placement_swap_2026-10-06';initial=root/'work/tseng_swapped_quality_gate_2026-10-06/design.route';stages=['trial_tseng_swapped_place_cold.py','verify_tseng_swapped_place_cold.py','trial_tseng_joint_native_import.py','verify_tseng_joint_native_import.py','trial_tseng_joint_canonical_reload.py','verify_tseng_joint_canonical_reload.py','trial_tseng_swapped_reference_canonical_reload.py','verify_tseng_swapped_reference_canonical_reload.py','trial_tseng_swapped_quality_gate.py','verify_tseng_swapped_quality_gate.py']
shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';sandboxes=[]
# Assemble and freeze both rounds before generating any new candidate.
for i,directory in enumerate((original,swapped,original,swapped)):
 sandbox=work/str(i);sandbox.mkdir();shutil.copytree(root/'tools',sandbox/'tools',ignore=shutil.ignore_patterns('__pycache__'));(sandbox/'build').symlink_to(root/'build',target_is_directory=True);(sandbox/'work').mkdir();(sandbox/'experiments').mkdir();(sandbox/'work/nonzero_rc_tseng_reference128_2026-10-06').symlink_to(root/'work/nonzero_rc_tseng_reference128_2026-10-06',target_is_directory=True)
 shutil.copytree(root/'experiments/nonzero_rc_tseng_reference128_2026-10-06',sandbox/'experiments/nonzero_rc_tseng_reference128_2026-10-06')
 for name in ('nonzero_rc_tseng_endpoints_2026-10-06','tseng_placement_swap_2026-10-06'):
  dest=sandbox/'experiments'/name;dest.mkdir()
  for f in ('endpoints.json','mapping.json'):shutil.copyfile(directory/f,dest/f)
  endpoint=json.loads((directory/'endpoints.json').read_text());shutil.copyfile(endpoint['inputs']['place']['path'],dest/'swapped.place')
 literal="root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'"
 for p in (sandbox/'tools').glob('*.py'):
  s=p.read_text().replace(literal,'Path('+repr(str(shared))+')')
  if p.name=='trial_tseng_joint_native_import.py':s=s.replace("shared=Path", "shutil.copyfile(endpoint_dir/'swapped.place',work/'design.place')\nshared=Path")
  if p.name=='verify_tseng_joint_native_import.py':s=s.replace("baseline=root/'experiments/nonzero_rc_tseng_reference128_2026-10-06'", "baseline=root/'experiments/tseng_swapped_place_cold_2026-10-06'")
  if 'reference_canonical_reload' in p.name:s=s.replace('tseng_swapped_native_import','tseng_joint_native_import')
  if 'swapped_quality_gate' in p.name:s=s.replace('tseng_swapped_canonical_reload','tseng_joint_canonical_reload')
  if p.name=='trial_tseng_joint_native_import.py':
   start=s.index("with (work/'identity.log').open('w')");end=s.index('nets={row',start)
   s=s[:start]+"from native_identity_cache import NativeIdentityCache\ncached_table,cache_info=NativeIdentityCache(Path("+repr(str(out/'cache'))+")).get(icmd,work);shutil.copyfile(cached_table,table);(work/'identity.log').write_text('Authenticated identity cache '+json.dumps(cache_info)+'\\n');\n"+s[end:]
   s=s.replace("'scope':'Pre-route", "'identity_cache':cache_info,'scope':'Pre-route")
  if p.name in ('trial_tseng_joint_canonical_reload.py','trial_tseng_swapped_reference_canonical_reload.py'):
   old="assert run(icmd,reload,reload/'identity.log',{**env,'ROUTECAST_NET_IDENTITY_FILE':str(table)})==1 and table.exists();"
   new="from native_identity_cache import NativeIdentityCache;cached_table,cache_info=NativeIdentityCache(Path("+repr(str(out/'cache'))+")).get(icmd,reload);shutil.copyfile(cached_table,table);(reload/'identity.log').write_text('Authenticated identity cache '+json.dumps(cache_info)+'\\n');"
   assert old in s;s=s.replace(old,new).replace("'pair_index':index,'post_sync_route_unchanged'", "'identity_cache':cache_info,'pair_index':index,'post_sync_route_unchanged'")
  p.write_text(s)
 # Standalone original XML path auditor, independent from context/search modules.
 prior=(root/'tools/verify_tseng_selected_reference_import.py').read_text();check=prior[prior.index('def check('):prior.index('inc=json.loads')]
 auditor='''import json,sys
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];ep=json.loads((root/'experiments/nonzero_rc_tseng_endpoints_2026-10-06/endpoints.json').read_text());graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)
'''+check+'''out=root/'experiments/tseng_joint_transfer_2026-10-06';snapshot=json.loads((out/'receipt.json').read_text());check(snapshot,ep);assert snapshot['failure'] is None and snapshot['completed_connections']==snapshot['required_connections']==1234
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'accepted_paths_checked':1234,'scope':'Independent originalXML physical path/endpoints/exactRC/tree/unioncapacity audit; no event optimality or budget claim for retained native paths.'},indent=2)+'\\n');print('verified1234 staged candidate paths')
'''
 (sandbox/'tools/audit_sequential_candidate.py').write_text(auditor);sandboxes.append(sandbox)
sources={n:sha(root/'tools'/n) for n in ('trial_tseng_sequential_cached4v2.py','persistent_rc_context.py','staged_placement_reroute.py','moved_history_repair_engine.py','native_route_ledger_import.py','accepted_route_state.py','native_identity_cache.py')}
p={'rounds':[{'sandbox':str(s),'endpoint_path':str(d/'endpoints.json'),'source_sha256':{n:sha(s/'tools'/n) for n in ['audit_sequential_candidate.py',*stages]}} for s,d in zip(sandboxes,(original,swapped,original,swapped))],'live_sources_sha256':sources,'initial_route_sha256':sha(initial),'endpoint_sha256':{str(d/'endpoints.json'):sha(d/'endpoints.json') for d in (original,swapped,original,swapped)},'cache_policy':'Fresh empty shared identity cache; miss and hit costs both included, no acceptance stage removed','policy':'Four fixed updates swapped→original→swapped→original→swapped, one persistentcontext, unchanged1ns/10000/max4 staged repair; each freshcold/native/canonical/quality decision and acceptedstate advancement. Stop on stage failure; no post-outcome budget changes.','scope':'Fresh fixed-input sequential update lifecycle; common pack/place/RR/toolbuild/initial acceptedreference generation and sandboxassembly excluded, initial context/ledger import included; no concurrent/durable publication or generalization claim.'}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[];begin=time.monotonic();t=time.monotonic();ctx=PersistentRCContext(swapped/'endpoints.json');owner=AcceptedRouteState(import_native_ledger(ctx,initial));setup=time.monotonic()-t;env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};completed=False
try:
 for i,(sandbox,directory) in enumerate(zip(sandboxes,(original,swapped,original,swapped))):
  round_start=time.monotonic();token=owner.token();t=time.monotonic();result=stage_reroute_with_repair(owner.state,directory/'endpoints.json');stage_s=time.monotonic()-t;assert owner.token()==token
  candidate=result['repair'] or result['incremental'];parent=sandbox/'experiments/tseng_joint_transfer_2026-10-06';parent.mkdir();(parent/'receipt.json').write_text(json.dumps(candidate,indent=2)+'\n')
  round_rows=[]
  for name in ['audit_sequential_candidate.py',*stages]:
   t=time.monotonic();log=out/f'round{i}_{name}.log'
   with log.open('w') as stream:code=subprocess.run(['python3',str(sandbox/'tools'/name)],cwd=sandbox,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
   round_rows.append({'tool':name,'exit_code':code,'wall_s':time.monotonic()-t,'log_sha256':sha(log)});print(i,name,code,flush=True)
   if code:raise RuntimeError('stage failed '+name)
  gate=sandbox/'experiments/tseng_swapped_quality_gate_2026-10-06';t=time.monotonic();prepared=owner.prepare(directory/'endpoints.json',gate/'selection.json',gate/'verification.json',token);owner.advance(prepared);advance_s=time.monotonic()-t
  state={'records':[owner.state.records[c] for c in sorted(owner.state.records)],'ledger':dict(owner.state.ledger),'scale':ctx.rc.scale,'graph_sha256':ctx.context[1],'failure':None,'completed_connections':1234,'required_connections':1234};statefile=out/f'accepted{i}.json';statefile.write_text(json.dumps(state,indent=2)+'\n')
  selection=json.loads((gate/'selection.json').read_text());rows.append({'round':i,'revision':owner.revision,'stage_s':stage_s,'acceptance_and_audit':round_rows,'prepare_advance_s':advance_s,'round_wall_s':time.monotonic()-round_start,'selected':selection['selected'],'candidate_cpd_ns':selection['predicted_cpd_ns'],'reference_cpd_ns':selection['reference_cpd_ns'],'accepted_state_sha256':sha(statefile),'selection_sha256':sha(gate/'selection.json'),'endpoint_path':str(directory/'endpoints.json')})
 completed=True
finally:
 r={'protocol_sha256':sha(out/'protocol.json'),'context_and_initial_import_s':setup,'rounds':rows,'completed':completed,'total_wall_s':time.monotonic()-begin};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print('completed',completed,'total',r['total_wall_s'],flush=True)
