"""Run complete unchanged audit bodies with a fresh process-local graph context."""
import ast
import json
import runpy
import sys
from pathlib import Path
from time import perf_counter
R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R/'tools'), str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from independent_audit_context_v1 import diagnostics
model = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
assert not output.exists(), 'new evidence directory required'
pairs = [('verify_resident_demand_frame_physical_v4.py','verify_resident_demand_frame_shared_context_v5.py'),
         ('verify_resident_events_round_schedule_cache_v6.py','verify_resident_events_shared_context_v7.py')]
# Compare the complete program AST after reversing exactly the two context edits.
for old,new in pairs:
    original = (R/'tools'/old).read_text()
    candidate = (R/'tools'/new).read_text().replace('from independent_audit_context_v1 import load_context','from immutable_xml_prediction_audit import ImmutableXMLAudit').replace("xml,ids,classes,switches,digest=load_context(graph,ep['graph_sha256'])", "xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,digest=read(graph)")
    assert ast.dump(ast.parse(original)) == ast.dump(ast.parse(candidate)), new
baseline_paths = [model/'initial_physical_verification.json', model/'sketch_physical_verification.json', model/'verification.json']
baselines = [json.loads(p.read_text()) for p in baseline_paths]
for proof in baselines:
    assert all(sha(p)==h for p,h in proof['bindings'].items())
assert diagnostics()['context_loads']==0
sources = [Path(__file__)] + [R/'tools'/name for pair in pairs for name in pair]
bindings = {**closure(sources), **{str(p):sha(p) for p in baseline_paths}}
output.mkdir(parents=True)
stages=[]
start=perf_counter()
for index,(script,args,name) in enumerate([
    (pairs[0][1],[str(model),'initial'],'initial_physical_verification.json'),
    (pairs[0][1],[str(model),'sketch'],'sketch_physical_verification.json'),
    (pairs[1][1],[str(model),model.name],'verification.json')]):
    target=output/name
    sys.argv=[str(R/'tools'/script),*args,str(target)]
    begin=perf_counter()
    runpy.run_path(str(R/'tools'/script),run_name='__main__')
    elapsed=perf_counter()-begin
    actual=json.loads(target.read_text())
    assert {k:v for k,v in actual.items() if k!='bindings'} == {k:v for k,v in baselines[index].items() if k!='bindings'}, name
    assert all(sha(p)==h for p,h in actual['bindings'].items())
    bindings.update(actual['bindings'])
    bindings[str(target)]=sha(target)
    stages.append(dict(audit=name,seconds=elapsed))
seconds=perf_counter()-start
stats=diagnostics()
assert stats['contexts']==stats['context_loads']==1 and stats['accesses']==3 and stats['independent_xml_parses']==2
assert all(sha(p)==h for p,h in bindings.items())
proof=dict(bindings=bindings,all_three_full_audit_outputs_equal=True,complete_audit_bodies_AST_preserved=True,
           fresh_independent_graph_context=True,diagnostics=stats,stages=stages,local_three_audit_and_comparison_seconds=seconds,
           scope='Local full-audit parity and timing only. Baseline authentication/setup before timer; archival hashes after timer. Not complete native workflow time, paired causal speedup, heldout, HDL or silicon proof.')
(output/'comparison.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({k:v for k,v in proof.items() if k!='bindings'},indent=2),flush=True)
