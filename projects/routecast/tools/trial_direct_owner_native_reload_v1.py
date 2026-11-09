"""Serialize complete verified model state and run original native FULL/STA analysis."""
import json,sys,shutil,subprocess,os,re
from pathlib import Path
from types import SimpleNamespace
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_route_ledger_import_compact import physical_paths
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from shared_rr_inventory import SharedRRInventory
from serialize_shared_inventory import serialize
from source_binding_v2 import closure
S=R/'experiments/direct_owner_global_wire_v1_2026-10-08';proof=S/'verification.json';p=json.loads(proof.read_text());assert all(sha(f)==h for f,h in p['bindings'].items())
receipt=json.loads((S/'receipt.json').read_text());command_source=R/'experiments/budget_repair_native_reload_v1_2026-10-08/protocol.json';native=json.loads(command_source.read_text());original_source=R/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128';target_place=R/'experiments/mux_budget_move_cohort_2026-10-06/w32_m2/target.place'
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
ep=Path(case['target']);meta=json.loads(ep.read_text());graph,digest,nodes,fields,rc,queries=load_endpoints(ep)
inventory=SharedRRInventory(SimpleNamespace(graph=graph,digest=digest,n=len(nodes),fields=fields))
assert p['all1929_events_and_complete_original_xml_fraction_frame_pass'] and p['all_dynamic_model_guards_pass']
needed={(u,v,s) for path in receipt['state'].values() for (u,_),(v,s) in zip(path,path[1:])};arcs={key:[] for key in needed}
for u in range(len(nodes)):
 for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
  key=(u,fields['dest_ranks'][slot],fields['switch_ids'][slot])
  if key in arcs:arcs[key].append(fields['edge_ids'][slot])
assert all(len(ids)==1 for ids in arcs.values())
records=[]
for q in queries:
 path=receipt['state'][str(q['connection_id'])];edges=[arcs[u,v,s][0] for (u,_),(v,s) in zip(path,path[1:])]
 rc.path(q['source'],q['sink'],edges);records.append({**q,'answer':{'physical_edge_ids':edges}})
D=R/'experiments/direct_owner_native_reload_v1_2026-10-08';D.mkdir(exist_ok=False)
inputs={**p['bindings'],str(proof):sha(proof),**closure([Path(__file__)]),str(command_source):sha(command_source)}
for name in ('design.blif','design.net'):
 source=original_source/name;inputs[str(source)]=sha(source);shutil.copyfile(source,D/name)
inputs[str(target_place)]=sha(target_place);shutil.copyfile(target_place,D/'design.place')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
identity=D/'identity.jsonl';ib=R/'build/native_net_identity_capture_2026-10-06';ir=json.loads((ib/'receipt.json').read_text());identity_binary=ib/'routecast_net_identity_vpr';assert sha(identity_binary)==ir['binary_sha256']
inputs[str(identity_binary)]=sha(identity_binary);inputs[str(ib/'receipt.json')]=sha(ib/'receipt.json')
icmd=native['command'].copy();icmd[0]=str(identity_binary);icmd[icmd.index('--route_file')+1]='missing.route'
with (D/'identity.log').open('w') as log:
 identity_code=subprocess.run(icmd,cwd=D,env={**env,'ROUTECAST_NET_IDENTITY_FILE':str(identity)},stdout=log,stderr=subprocess.STDOUT).returncode
assert identity_code==1 and identity.exists();inputs[str(identity)]=sha(identity)
text,pins=serialize({'records':records},ep,identity,D/'design.place',inventory);route=D/'design.route';route.write_text(text)
actual=Counter((name,path) for name,paths in physical_paths(route).items() for path in paths)
expected=Counter((meta['net_names'][str(q['net_id'])],tuple(tuple(x) for x in receipt['state'][str(q['connection_id'])])) for q in queries);assert actual==expected
cmd=native['command'].copy();cmd[0]=str(R/'build/native_reconciled_dump_v1_2026-10-08/verbose_sync_vpr');br=json.loads((R/'build/native_reconciled_dump_v1_2026-10-08/receipt.json').read_text());assert sha(cmd[0])==br['binary_sha256'];inputs[str(Path(cmd[0]))]=sha(cmd[0]);assert '--analysis' in cmd
(D/'protocol.json').write_text(json.dumps(dict(inputs=inputs,command=cmd,serialized_route_sha256=sha(route),terminal_bindings=pins,identity_command=icmd,identity_exit_code=identity_code,scope='Fresh candidate serialized against newly captured original packed netlist and target placement identity. No prior canonical packed netlist/place/identity input consumed. Original budget failures retained; native/canonical/HDL checks remain separate.'),indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
with (D/'reload.log').open('w') as log:code=subprocess.run(cmd,cwd=D,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
log=(D/'reload.log').read_text();assert all(sha(f)==h for f,h in inputs.items())
cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)
report=dict(protocol_sha256=sha(D/'protocol.json'),exit_code=code,full_consistency_pass='Completed routing consistency check successfully.' in log,vpr_succeeded='VPR succeeded' in log,cpd_ns=cpd[-1] if cpd else None,log_sha256=sha(D/'reload.log'),files={str(f):sha(f) for f in D.iterdir() if f.is_file()},scope='Native acceptance result only; pin reconciliation counters and independent final physical/model budgets still require inspection.')
(D/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='files'})
