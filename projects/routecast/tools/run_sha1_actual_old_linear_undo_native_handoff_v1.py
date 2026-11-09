"""Complete fresh demand model followed by current-context seed serialization."""
import ast, json, sys, time
from pathlib import Path
from collections import Counter, defaultdict
R = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from run_resident_actual_old_linear_undo_model_v13 import predict
from resident_native_inventory_v2 import Inventory
from serialize_whole_net_subset_pin_index_v2 import serialize_subset

case = sys.argv[1]
assert case=='sha1'
admission=R/'experiments/sha1_frozen_model_v1_2026-10-10/verification.json'
proof=json.loads(admission.read_text())
assert proof['complete_candidate_physical_and_events_pass']
assert all(sha(p)==h for p,h in proof['bindings'].items())
candidate_admission=admission
epfile=Path(sys.argv[2]).resolve()
ep = json.loads(epfile.read_text())
assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values())
selector = R/'tools/select_resident_native_seed_subset_v1.py'
bindings = {**closure([Path(__file__),selector]),str(admission):sha(admission),str(candidate_admission):sha(candidate_admission),str(epfile):sha(epfile),
            **{v['path']:v['sha256'] for v in ep['inputs'].values()}}
D=Path(sys.argv[3]).resolve();native=Path(sys.argv[4]).resolve();model=Path(sys.argv[5]).resolve()
D.mkdir(parents=True);native.mkdir(parents=True,exist_ok=True)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,case=case,
    scope='Fresh complete model from authenticated development endpoint. Current-arm graph retained, unchanged whole-NET selector, no historical model/seed read for decisions. All original pending queries retained. Model plus context adapter, selection, serialization and output included in local pipeline clock. No input acquisition, independent audits, exact native routing or canonical reload in this timing; not full workflow gain. No heldout or silicon claim.'),indent=2)+'\n')
begin=time.perf_counter()
tick=time.perf_counter();result,context=predict(epfile,model,retain_context=True)
model_seconds=time.perf_counter()-tick
tick=time.perf_counter();inv=Inventory(*context);adapter_seconds=time.perf_counter()-tick
tick=time.perf_counter();c=json.loads((model/'sketch.json').read_text())
assert c['completed_connections']==c['required_connections']==len(ep['connections'])
assert {x['connection_id'] for x in c['records']}=={x['connection_id'] for x in ep['connections']}
tree=ast.parse(selector.read_text());loop=next(n for n in tree.body if isinstance(n,ast.For))
start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='rec')
stop=next(i for i,n in enumerate(loop.body) if i>start and isinstance(n,ast.Assert))
scope=dict(c=c,ep=ep,xml=inv,groups=defaultdict(list),Counter=Counter)
exec(compile(ast.Module(body=loop.body[start:stop],type_ignores=[]),str(selector),'exec'),scope)
records,pending=scope['records'],scope['pending']
selected={r['connection_id'] for r in records};allids={q['connection_id'] for q in ep['connections']}
assert len(selected)==len(records) and not selected.intersection(pending) and selected|set(pending)==allids
assert Counter(node for net in scope['kept'] for node in scope['owners'][net])==scope['ledger']
assert all(value<=inv.graph.nodes[node].capacity for node,value in scope['ledger'].items())
payload=dict(records=records,pending=pending,decisions=scope['decisions'])
text,pins=serialize_subset(dict(records=records),epfile,Path(ep['inputs']['native_identity']['path']),Path(ep['inputs']['place']['path']),inv)
(native/'subset.json').write_text(json.dumps(payload)+'\n')
(native/'seed.route').write_text(text)
(native/'bindings.json').write_text(json.dumps(pins)+'\n')
selection_serialization_output_seconds=time.perf_counter()-tick
assert all(sha(p)==h for p,h in bindings.items())
continuous_pipeline_seconds=time.perf_counter()-begin
out=dict(bindings=bindings,model_result=result,required_connections=len(allids),selected_connections=len(records),
         pending_connections=len(pending),model_subcall_seconds=model_seconds,adapter_seconds=adapter_seconds,
         selection_serialization_output_seconds=selection_serialization_output_seconds,
         continuous_local_pipeline_seconds=continuous_pipeline_seconds,
         files={**{str(p):sha(p) for p in model.rglob('*') if p.is_file()},**{str(native/n):sha(native/n) for n in ['subset.json','seed.route','bindings.json']},str(D/'protocol.json'):sha(D/'protocol.json')},
         scope='Local model/context handoff/selection/serialization only. Final archival hashing after local timer, original source reauthentication included. Independent physical/event/native/canonical validation still required. No full workflow performance claim.')
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','files']},indent=2),flush=True)
