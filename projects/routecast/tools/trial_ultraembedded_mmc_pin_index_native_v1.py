"""Execute candidate canonical pin index with full native and independent gates."""
import json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from shared_compact_native_inventory_v1 import Inventory
from canonical_reload_pin_index_v2 import canonical_reload,binary,identity
base=R/'experiments/ultraembedded_mmc_continuous_workflow_v2_2026-10-08/seed'
proof_path=R/'experiments/ultraembedded_mmc_pin_index_equivalence_v1_2026-10-08/verification.json'
proof=json.loads(proof_path.read_text());assert proof['all_sink_occurrences']==115572 and proof['complete_canonical_route_byte_identical']
assert all(sha(k)==v for k,v in proof['bindings'].items())
native=base/'native/mmc';receipt=json.loads((native/'receipt.json').read_text())
for section in ('bindings','files'):
 assert all(sha(k)==v for k,v in receipt.get(section,{}).items())
out=R/'experiments/ultraembedded_mmc_pin_index_native_v1_2026-10-08';out.mkdir()
bindings={**closure([Path(__file__),R/'tools/native_resume_prototype/canonical_reload_pin_index_v2.py']),str(proof_path):sha(proof_path),str(native/'receipt.json'):sha(native/'receipt.json'),str(binary):sha(binary),str(identity):sha(identity)}
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Fresh candidate native canonical reload full original graph, all physical sequences, packed bytes, ignored membership, FULL/STA; no paired speed or whole workflow gain.'),indent=2)+'\n')
graph=Path(receipt['command'][receipt['command'].index('--read_rr_graph')+1]);tick=time.perf_counter()
inv=Inventory(graph)
candidate=dict(files=receipt['files'],command=receipt['command'],width=128,decision='R',cpd_ns=receipt['diagnostic_cpd_ns'])
try:
 result=canonical_reload(candidate,native,out/'mmc',inv)
 assert result['semantic_consistency_gate_pass']
 assert (out/'mmc/design.route').read_bytes()==(base/'canonical/mmc/design.route').read_bytes()
 assert all(sha(k)==v for k,v in bindings.items())
 data=dict(bindings=bindings,rows=[dict(name='mmc',mode='seed',status='SEMANTIC_CANONICAL_PASS',canonical=result)],candidate_canonical_route_byte_identical=True,elapsed_seconds=time.perf_counter()-tick,scope='Candidate full native canonical execution passed; independent ignored-pin proof remains separate, no speed/stability gain.')
except Exception as error:
 (out/'failure.json').write_text(json.dumps(dict(error=repr(error),elapsed_seconds=time.perf_counter()-tick),indent=2)+'\n');raise
(out/'receipt.json').write_text(json.dumps(data,indent=2)+'\n');print('candidate native canonical PASS',flush=True)
