"""Complete fresh demand model followed by current-context seed serialization."""
import ast, json, sys, time, os
from pathlib import Path
from collections import Counter, defaultdict
R = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from run_native_live_seed_adaptive_width_model_v1 import predict
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
    scope='Fresh complete model from authenticated development endpoint. Current-arm graph retained, unchanged whole-NET selector, no historical model/seed read for decisions. All original pending queries retained. Model/context adapter/selection/serialization, independent model audits and same-resident native seed routing included in local pipeline clock. Input acquisition and final native physical/canonical audits are outer arm stages; not full workflow gain. No heldout or silicon claim.'),indent=2)+'\n')
begin=time.perf_counter()
os.environ['ROUTECAST_LIVE_WORK']=str(native);os.environ['ROUTECAST_LIVE_DEFER_SEED']='1';os.environ['ROUTECAST_LIVE_ENDPOINT']=str(epfile)
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
import subprocess
with (D/'full_model_audits.log').open('w') as log:subprocess.run([sys.executable,str(R/'tools/run_shared_overflow_guard_audits_v1.py'),str(model),case],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
shared=json.loads((model/'shared_audit_receipt.json').read_text());assert shared['all_three_complete_audits_pass'] and all(sha(p)==h for p,h in shared['bindings'].items())
from native_live_seed_adaptive_width_adapter_v1 import ACTIVE
assert ACTIVE is not None and ACTIVE.proc.poll() is None
ACTIVE.bindings.update({str(model/'shared_audit_receipt.json'):sha(model/'shared_audit_receipt.json')});ACTIVE.finish(native/'seed.route')

assert all(sha(p)==h for p,h in bindings.items())
continuous_pipeline_seconds=time.perf_counter()-begin
out=dict(bindings=bindings,model_result=result,required_connections=len(allids),selected_connections=len(records),
         pending_connections=len(pending),model_subcall_seconds=model_seconds,adapter_seconds=adapter_seconds,
         selection_serialization_output_seconds=selection_serialization_output_seconds,
         continuous_local_pipeline_seconds=continuous_pipeline_seconds,
         files={**{str(p):sha(p) for p in model.rglob('*') if p.is_file()},**{str(native/n):sha(native/n) for n in ['subset.json','seed.route','bindings.json']},str(D/'protocol.json'):sha(D/'protocol.json'),str(native/'service_receipt.json'):sha(native/'service_receipt.json')},
         scope='Local model/context handoff/selection/serialization/full model audits/resident seed import and native completion. Final archival hashing after local timer, original source reauthentication included. Model physical/event audits included; final native physical/canonical validation still required. No full workflow performance claim.')
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','files']},indent=2),flush=True)
