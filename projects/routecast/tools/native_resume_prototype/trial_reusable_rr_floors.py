"""All-target placement sequence, charging first context construction and every update."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from freeze_priority_family import closure
ROOT=Path(__file__).resolve().parents[2];w=int(sys.argv[1]);assert w in (16,32);out=ROOT/f'experiments/native_resume_reusable_rr_floors_w{w}_2026-10-07';out.mkdir(exist_ok=False);start=time.perf_counter()
build=ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/receipt.json';b=json.loads(build.read_text());assert sha(b['binary'])==b['binary_sha256'];sequence=[0,1,2,3,0];eps=[ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json' for i in sequence]
p=dict(sequence=sequence,endpoints={str(f):sha(f) for f in eps},sources=closure([Path(__file__)]),build_receipt_sha256=sha(build),scope='Full target queries in fixed placement-state sequence m0,m1,m2,m3,m0, each existing state originally derived from common seed. Graph/model/pair cache; one construction paid plus all validations/export/misses. No native runtime snapshot, repair or full route proofs in this component trial.')
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');ctx=ReusableRRFloors(eps[0],b['binary'],out/'context');rows=[]
for i,ep in zip(sequence,eps):
 r=ctx.query(ep);rows.append(dict(index=i,epoch=r['epoch'],connections=r['required_connections'],miss_pairs=r['miss_pairs'],hit_connections=r['hit_connections'],cache_entries=r['cache_entries'],seconds=r['total_seconds'],receipt_sha256=sha(out/f"context/epoch_{r['epoch']}/receipt.json")));print(w,rows[-1],flush=True)
assert all(sha(f)==h for f,h in p['endpoints'].items());assert rows[-1]['miss_pairs']==0
# Invalid endpoint graph and malformed identities must not publish or modify cache.
before=(ctx.epoch,len(ctx._cache));bad=json.loads(eps[-1].read_text());bad['graph_sha256']='0'*64;f=out/'wrong_graph.json';f.write_text(json.dumps(bad))
try:ctx.query(f);raise AssertionError('expected rejection')
except ValueError:pass
assert before==(ctx.epoch,len(ctx._cache))
bad=json.loads(eps[-1].read_text());bad['connections'][0]['source']=ctx.n;f=out/'wrong_endpoint.json';f.write_text(json.dumps(bad))
try:ctx.query(f);raise AssertionError('expected rejection')
except ValueError:pass
assert before==(ctx.epoch,len(ctx._cache))
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),construction_seconds=ctx.construction_seconds,rows=rows,trial_seconds=time.perf_counter()-start,invalid_inputs_rejected_without_publication=True,context_bindings=ctx.bindings,scope=p['scope']+'; in-memory synchronous single-owner cache, no durable/concurrent-writer guarantee. Component time is not net route gain.'),indent=2)+'\n');print(w,'finished',time.perf_counter()-start,flush=True)
