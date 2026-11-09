import json,sys,time
from pathlib import Path
R=Path.cwd();sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from canonical_reload_ignored_invariants_v1 import canonical_reload,binary,identity
from shared_compact_native_inventory_v1 import Inventory
out=R/'experiments/aes_ignored_invariant_canonical_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__)]),str(binary):sha(binary),str(identity):sha(identity)};rows=[]
(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'scope':'New explicit native semantic consistency gate, preserves original zero-counter failure. All four observed native source outputs. No model/QoR/time/heldout success implied.'},indent=2)+'\n')
for trial in ['aes_ignored_seed_admission_v1_2026-10-08','aes_cold_partition_audit_v1_2026-10-08']:
 receipt=R/'experiments'/trial/'receipt.json';d=json.loads(receipt.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());bindings[str(receipt)]=sha(receipt)
 for candidate in d['rows']:
  start=time.perf_counter();name=candidate['name'];src=receipt.parent/name;graph=Path(candidate['command'][candidate['command'].index('--read_rr_graph')+1]);result=canonical_reload({**candidate,'width':128,'decision':'R'},src,out/(trial+'_'+name),Inventory(graph));assert result['semantic_consistency_gate_pass'] and not result['original_zero_counter_gate_pass'];rows.append({'trial':trial,'name':name,'canonical':result,'seconds':time.perf_counter()-start});(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(trial,name,'INVARIANTS_PASS','zero_counter_gate',result['original_zero_counter_gate_pass'],flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n')
