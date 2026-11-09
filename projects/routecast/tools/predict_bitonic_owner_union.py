"""All-case initial owner-union predictor, no native routes or labels read by search."""
import json,time
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from owner_union_wire_rc_context_cached import OwnerUnionWireRCContext
from owner_union_initial_prediction_engine import predict_joint
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/bitonic_physical_endpoints_2026-10-07';out=ROOT/'experiments/bitonic_owner_union_prediction_2026-10-07';r=json.loads((base/'receipt.json').read_text());out.mkdir();names=['owner_union_initial_prediction_engine.py','owner_union_wire_rc_context_cached.py','wire_penalty_rc_context_cached.py','persistent_rc_context_cached.py','cached_rr_endpoint_context.py','integer_rc_context_memo.py','native_capacity_rc_search.py','nonzero_rc_endpoint_context_memo.py'];sources={str(ROOT/'tools'/n):sha(ROOT/'tools'/n) for n in names};sources[str(Path(__file__))]=sha(Path(__file__))
inputs={str(base/f'n{n}/endpoints.json'):sha(base/f'n{n}/endpoints.json') for n in [4,8,16]};protocol=dict(sources=sources,inputs=inputs,cohort=[4,8,16],weight_ns='1/20',max_labels=10000,connection_cap_ns=1,fallback_limit=0,order='ascending NET and CID',scope='Frozen before initial predictions, owner cost already frozen before native capture. New initial orchestration freezes AFTER native reference availability: not fully prospective source-complete heldout proof. No native route/delay/occupancy read by driver or search; pre-route endpoints only. No repair/minimum-delay fallback, all failures retained, not incremental move acceptance. Fixed1ns/50ps inherited, no tuning.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for n in protocol['cohort']:
 ep=base/f'n{n}/endpoints.json';assert sha(ep)==inputs[str(ep)];start=time.perf_counter();ctx=OwnerUnionWireRCContext(ep,weight_ns=Fraction(1,20));setup=time.perf_counter()-start;start=time.perf_counter();candidate=predict_joint(ctx,max_labels=10000,fallback_limit=0);seconds=time.perf_counter()-start;file=out/f'n{n}.json';file.write_text(json.dumps(candidate,indent=2)+'\n');rows.append(dict(count=n,status=candidate['status'],completed=candidate['completed_connections'],required=candidate['required_connections'],failure=candidate['failure'],setup_seconds=setup,search_seconds=seconds,candidate_sha256=sha(file)));print(rows[-1],flush=True)
assert all(sha(f)==h for f,h in sources.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,complete=True),indent=2)+'\n')
