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
S=R/'experiments/budget_occupied_branch_repair_v1_2026-10-08';proof=S/'complete_frame_verification_v2.json';p=json.loads(proof.read_text());assert all(sha(f)==h for f,h in p['bindings'].items())
receipt=json.loads((S/'receipt.json').read_text());old=R/'experiments/native_resume_branch_partial_v8_2026-10-08';native=json.loads((old/'repair_verification.json').read_text());canonical=old/'resume/canonical'
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
ep=Path(case['target']);meta=json.loads(ep.read_text());graph,digest,nodes,fields,rc,queries=load_endpoints(ep)
inventory=SharedRRInventory(SimpleNamespace(graph=graph,digest=digest,n=len(nodes),fields=fields))
byid={x['connection_id']:x for x in p['rows']};records=[{**q,'answer':{'physical_edge_ids':byid[q['connection_id']]['physical_edge_ids']}} for q in queries]
D=R/'experiments/budget_repair_native_reload_v1_2026-10-08';D.mkdir(exist_ok=False)
inputs={**p['bindings'],str(proof):sha(proof),**closure([Path(__file__)]),str(old/'repair_verification.json'):sha(old/'repair_verification.json')}
for name in ('design.blif','design.net','design.place'):
 source=canonical/name;inputs[str(source)]=sha(source);shutil.copyfile(source,D/name)
identity=canonical/'identity.jsonl';inputs[str(identity)]=sha(identity)
text,pins=serialize({'records':records},ep,identity,D/'design.place',inventory);route=D/'design.route';route.write_text(text)
actual=Counter((name,path) for name,paths in physical_paths(route).items() for path in paths)
expected=Counter((meta['net_names'][str(q['net_id'])],tuple(tuple(x) for x in receipt['state'][str(q['connection_id'])])) for q in queries);assert actual==expected
cmd=native['canonical']['command'];inputs[str(Path(cmd[0]))]=sha(cmd[0]);assert '--analysis' in cmd
(D/'protocol.json').write_text(json.dumps(dict(inputs=inputs,command=cmd,serialized_route_sha256=sha(route),terminal_bindings=pins,scope='Complete model candidate native analysis; original two infeasible budgets remain; no native routing/performance gain'),indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
with (D/'reload.log').open('w') as log:code=subprocess.run(cmd,cwd=D,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
log=(D/'reload.log').read_text();assert all(sha(f)==h for f,h in inputs.items())
cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)
report=dict(protocol_sha256=sha(D/'protocol.json'),exit_code=code,full_consistency_pass='Completed routing consistency check successfully.' in log,vpr_succeeded='VPR succeeded' in log,cpd_ns=cpd[-1] if cpd else None,log_sha256=sha(D/'reload.log'),files={str(f):sha(f) for f in D.iterdir() if f.is_file()},scope='Native acceptance result only; pin reconciliation counters and independent final physical/model budgets still require inspection.')
(D/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='files'})
