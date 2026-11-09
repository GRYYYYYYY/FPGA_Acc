"""Frozen wholeNET selector/current-pin serializer for certified MMC raw frame."""
import ast,json,time,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
D=R/'experiments/mmc_native_local_seed_v1_2026-10-18';D.mkdir(exist_ok=False);start=time.perf_counter();F=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18';pp=R/'experiments/mmc_native_cached_feedback_audits_v1_2026-10-18/verification.json';v=json.loads(pp.read_text());assert v['all_three_frame_and_complete_event_audits_pass'] and all(sha(p)==h for p,h in v['bindings'].items());epfile=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json';ep=json.loads(epfile.read_text());frame=F/'model/sketch.json';c=json.loads(frame.read_text());selector=R/'tools/select_resident_native_seed_subset_v1.py';bindings={**closure([Path(__file__),selector]),str(pp):sha(pp),str(frame):sha(frame),str(epfile):sha(epfile)}
for spec in ep['inputs'].values():assert sha(spec['path'])==spec['sha256'];bindings[spec['path']]=spec['sha256']
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,policy='Same frozen completeNET selector: descending requested connection count, ascending unique tree-node count, numeric NET ID. No native target outcome inputs. All rejected NET connections pending. Cached old floors inherit the explicit source-contract scope; selector/serializer do not use floor values.',scope='Seed only, not native completion or speed result.'),f,indent=2);f.write('\n')
print('MMC LOCAL SEED INVENTORY START',flush=True);xml=Inventory(Path(ep['inputs']['graph']['path']));xml.validate(Path(ep['inputs']['graph']['path']),ep['graph_sha256']);tree=ast.parse(selector.read_text());loop=next(n for n in tree.body if isinstance(n,ast.For));begin=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='rec');end=next(i for i,n in enumerate(loop.body) if i>begin and isinstance(n,ast.Assert));selection=compile(ast.Module(body=loop.body[begin:end],type_ignores=[]),str(selector),'exec');scope=dict(c=c,ep=ep,xml=xml,groups=defaultdict(list),Counter=Counter);exec(selection,scope);records=scope['records'];pending=scope['pending'];ids={r['connection_id'] for r in records};allids={q['connection_id'] for q in ep['connections']};assert len(ids)==len(records) and not ids.intersection(pending) and ids|set(pending)==allids;ledger=Counter(n for net in scope['kept'] for n in scope['owners'][net]);assert ledger==scope['ledger'] and all(v<=xml.graph.nodes[n].capacity for n,v in ledger.items());print('MMC LOCAL SELECTION',len(ids),'selected',len(pending),'pending',flush=True)
text,pins=serialize_subset(dict(records=records),epfile,Path(ep['inputs']['native_identity']['path']),Path(ep['inputs']['place']['path']),xml)
for name,data in [('seed.route',text),('subset.json',json.dumps(dict(records=records,pending=pending,decisions=scope['decisions']))+'\n'),('pin_bindings.json',json.dumps(pins)+'\n')]:
 with (D/name).open('x') as f:f.write(data)
 bindings[str(D/name)]=sha(D/name)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings=bindings,selected_connections=len(ids),pending_connections=len(pending),selected_nets=len(scope['kept']),preparation_seconds=time.perf_counter()-start,complete_partition_and_capacity_pass=True,independent_audit_pending=True,scope='Production subset and current-pin seed serialization; full required connection count115572 preserved. Independent selected paths/pins/occupancy audit and native completion pending.'),f,indent=2);f.write('\n')
print('MMC LOCAL SEED GENERATED',len(ids),len(pending),flush=True)
