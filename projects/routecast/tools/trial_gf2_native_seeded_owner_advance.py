"""Single synchronous owner advancement, complete selected path parity and stale guard."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger,physical_paths
from accepted_route_state import AcceptedRouteState,state_digest
from immutable_xml_prediction_audit import ImmutableXMLAudit
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_native_seeded_owner_advance_2026-10-06';out.mkdir();cases=[]
for w in (32,64,128):
 selected=root/f'experiments/gf2_d{w}_native_seeded_quality_gate_2026-10-06';cases.append({'width':w,'selection':str(selected/'selection.json'),'verification':str(selected/'verification.json'),'bindings':{str(p):sha(p) for p in (selected/'selection.json',selected/'verification.json',selected/'protocol.json')}})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'sources_sha256':{n:sha(root/'tools'/n) for n in ('accepted_route_state.py','native_route_ledger_import.py','persistent_rc_context.py')},'scope':'Fresh native original-layout single owner prepare/advance into selected swapped layout. In-memory synchronous only, no concurrent/durable publication. Both fallback/candidate branches retained.'},indent=2)+'\n');rows=[]
for c in cases:
 w=c['width'];ep=root/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{w}/endpoints.json';swap=root/f'experiments/gf2_d{w}_placement_swap_2026-10-06/endpoints.json';route=root/f'work/gf2_d{w}_fixed_original_cold_2026-10-06/design.route';ctx=PersistentRCContext(ep);owner=AcceptedRouteState(import_native_ledger(ctx,route));token=owner.token();t=time.monotonic();prepared=owner.prepare(swap,c['selection'],c['verification'],token);assert owner.token()==token;owner.advance(prepared);wall=time.monotonic()-t;assert owner.revision==1 and ctx.endpoint_metadata==json.loads(swap.read_text()) and not ctx.history
 selection=json.loads(Path(c['selection']).read_text());selected_route=next(Path(n) for n in selection['files_sha256'] if Path(n).name=='design.route');native=physical_paths(selected_route);graph=Path(ctx.endpoint_metadata['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ctx.endpoint_metadata['graph_sha256']);actual={}
 for rec in owner.state.records.values():
  path=[(rec['source'],None)]
  for eid in rec['answer']['physical_edge_ids']:
   e=xml.graph.edges[eid];assert e.source==path[-1][0];path.append((e.sink,e.switch_id))
  actual.setdefault(ctx.endpoint_metadata['net_names'][str(rec['net_id'])],[]).append(tuple(path))
 assert {n:sorted(v) for n,v in native.items() if v}=={n:sorted(v) for n,v in actual.items()};assert all(d<=xml.caps[n] for n,d in owner.state.ledger.items());advanced=owner.token()
 try:owner.advance(prepared)
 except ValueError:pass
 else:raise AssertionError('consumed result advanced twice')
 assert owner.token()==advanced
 for f,h in c['bindings'].items():assert sha(f)==h
 snapshot={'revision':owner.revision,'records':[owner.state.records[cid] for cid in sorted(owner.state.records)],'ledger':dict(owner.state.ledger),'endpoint_metadata':ctx.endpoint_metadata};file=out/f'gf2_d{w}_accepted.json';file.write_text(json.dumps(snapshot,indent=2)+'\n');rows.append({'width':w,'selected':selection['selected'],'selected_cpd_ns':selection['selected_cpd_ns'],'revision':owner.revision,'connections':len(owner.state.records),'selected_physical_paths_exact':True,'prepare_leaves_live_state_unchanged':True,'consumed_result_rejected':True,'state_digest':state_digest(owner.state),'snapshot_sha256':sha(file),'prepare_advance_s':wall,'scope':'Single in-memory owner only'});print(rows[-1],flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':True},indent=2)+'\n')
