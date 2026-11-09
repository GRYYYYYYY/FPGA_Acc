"""Actual96 graph semantic reload after authenticated complete physical success."""
import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from canonical_reload_pin_index_expat_v3 import canonical_reload,binary,identity
from shared_compact_native_inventory_v1 import Inventory
S=R/'experiments/sha1_native_abort_policy_v1_2026-10-10';src=S/'96';proof=src/'physical_verification_v1.json';v=json.loads(proof.read_text());assert v['all_original_XML_physical_queries_branch_arcs_and_capacity_pass'] and all(sha(k)==h for k,h in v['bindings'].items())
rp=S/'receipt.json';r=json.loads(rp.read_text());row=next(x for x in r['rows'] if x['width']==96);assert row['exit_code']==0 and all(sha(k)==h for k,h in row['files'].items())
protocol=S/'protocol.json';p=json.loads(protocol.read_text());cmd=next(x['command'] for x in p['cases'] if x['width']==96).copy();graph=Path(cmd[cmd.index('--read_rr_graph')+1])
D=R/'experiments/sha1_abort_policy96_canonical_v1_2026-10-10';D.mkdir();bindings={**closure([Path(__file__)]),str(proof):sha(proof),str(rp):sha(rp),str(protocol):sha(protocol),str(graph):sha(graph),str(binary):sha(binary),str(identity):sha(identity)}
cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',(src/'native.log').read_text())[-1]);candidate=dict(files=row['files'],command=cmd,width=96,decision='R',cpd_ns=cpd)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,candidate=candidate,scope='Original96 physical route reload, original read-graph and policy flags retained for analysis only. No rerouting/model decision. Original zero-counter gate retained.'),indent=2)+'\n')
result=canonical_reload(candidate,src,D/'96',Inventory(graph));assert result['semantic_consistency_gate_pass'] and all(sha(k)==h for k,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=[dict(name='96',mode='cold',status='SEMANTIC_CANONICAL_PASS',canonical=result)]),indent=2)+'\n');print('PASS96 canonical',result['mismatches'],result['original_zero_counter_gate_pass'])
