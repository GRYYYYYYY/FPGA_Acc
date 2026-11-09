"""All current-model physical frames and events independently audited in one process."""
import ast
import json
import runpy
import sys
from pathlib import Path
from time import perf_counter
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from independent_audit_context_v1 import diagnostics
from independent_fraction_arc_context_v2 import diagnostics as cache_diagnostics
model=Path(sys.argv[1]).resolve();name=sys.argv[2]
pairs=[('verify_resident_demand_frame_physical_v4.py','verify_resident_demand_frame_direct_lattice_v7.py'),('verify_resident_events_actual_old_joint_fallback_linear_v9_no_span.py','verify_resident_events_actual_old_linear_direct_lattice_v12_no_span.py')]
sources=[Path(__file__)]+[R/'tools'/n for pair in pairs for n in pair]
bindings=closure(sources)
contract=R/'experiments/independent_fraction_arc_cache_contract_v1_2026-10-10/verification.json'
cp=json.loads(contract.read_text());assert cp['pass_all'] and all(sha(p)==h for p,h in cp['bindings'].items())
bindings[str(contract)]=sha(contract)
direct_contract=R/'experiments/exact_rc_lattice_direct_pairs_contract_v2_2026-10-10/verification.json'
dc=json.loads(direct_contract.read_text());assert dc['pass_all'] and dc['random_contexts']==200 and all(sha(p)==h for p,h in dc['bindings'].items())
bindings[str(direct_contract)]=sha(direct_contract)
for old,new in pairs:
 original=(R/'tools'/old).read_text()
 candidate=(R/'tools'/new).read_text().replace('from exact_rc_lattice_direct_pairs_v2 import exact_scale','from exact_rc_lattice_unique_pairs_v1 import exact_scale').replace('from independent_fraction_arc_context_v2 import load_context','from immutable_xml_prediction_audit import ImmutableXMLAudit').replace('from buffered_rc_node_classes import read\nfrom independent_fraction_arc_context_v2 import arc_delay','from buffered_rc_node_classes import read,arc_delay').replace("xml,ids,classes,switches,digest=load_context(graph,ep['graph_sha256'])","xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,digest=read(graph)")
 assert ast.dump(ast.parse(original))==ast.dump(ast.parse(candidate))
assert diagnostics()['context_loads']==0
stages=[];start=perf_counter()
for script,args,filename in [(pairs[0][1],[str(model),'initial'],'initial_physical_verification.json'),(pairs[0][1],[str(model),'sketch'],'sketch_physical_verification.json'),(pairs[1][1],[str(model),name],'verification.json')]:
 target=model/filename
 assert not target.exists(),'new current-model audit outputs required'
 sys.argv=[str(R/'tools'/script),*args,str(target)]
 begin=perf_counter();runpy.run_path(str(R/'tools'/script),run_name='__main__')
 stages.append(dict(audit=filename,seconds=perf_counter()-begin))
 proof=json.loads(target.read_text())
 assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
 assert all(sha(p)==h for p,h in proof['bindings'].items())
 bindings.update(proof['bindings']);bindings[str(target)]=sha(target)
assert proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
assert proof['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
stats=diagnostics();assert stats['contexts']==stats['context_loads']==1 and stats['accesses']==3 and stats['independent_xml_parses']==2
assert all(sha(p)==h for p,h in bindings.items())
cache_stats=cache_diagnostics();assert cache_stats['contexts']==1 and cache_stats['hits']>0 and cache_stats['misses']==cache_stats['entries']
result=dict(cache_diagnostics=cache_stats,bindings=bindings,all_three_complete_audits_pass=True,complete_audit_bodies_AST_preserved=True,fresh_independent_graph_context=True,diagnostics=stats,stages=stages,local_seconds=perf_counter()-start,scope='Current-model independent full XML physical frames and complete event replay. Graph inputs alone shared within this process; no historical predictions or native labels read. Outer subprocess stage must be included in complete workflow timer.')
(model/'shared_audit_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)
