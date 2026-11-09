"""Pre-run source/invariant lineage check, not runtime or full-event audit."""
import json,difflib,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path.cwd();old=R/'tools/run_present_overflow_guard_model_v1.py';new=R/'tools/run_criticality_present_overflow_guard_model_v1.py';a=old.read_text();b=new.read_text();ast.parse(b)
def span(text,start,end):return text[text.index(start):text.index(end,text.index(start))]
x=span(a,' for net,qs in sorted(groups.items()):',' ledger=Counter(n for owned in owners.values()')
y=span(b,' for net,qs in sorted(groups.items()):',' ledger=Counter(n for owned in owners.values()').replace('search_seconds','cpp_search_seconds')
assert x==y,'initial floor/path/budget code changed'
x=span(a,'    if pressure_delta>0:','  check_tick=time.perf_counter()')
y=span(b,'    if pressure_delta>0:','  check_tick=time.perf_counter()')
assert x==y,'overflow rejection/commit/epoch/context finish changed'
assert 'search.prepare({},0,structural=False)' in b
assert 'criticality_primary(criticality_graph,qs,records[net],criticalities,ObjectivePrices()' in b
assert 'fallback(f,rc,slots,qs,old,parents,settled,snapshot,1,node_base,criticalities,10000)' in b
assert 'prepare_admission(f,rc,slots,qs,old,candidate,ledger)' in b
contracts=['criticality_per_query_price_cache_contract_v1','criticality_ordered_net_random_contract_v1','criticality_resident_joint_adapter_contract_v2','criticality_net_admission_random_contract_v1','criticality_net_parent_conflict_contract_v1']
bindings={str(p):sha(p) for p in [old,new,Path(__file__).resolve()]}
for name in contracts:
 p=R/'experiments'/(name+'_2026-10-10')/'verification.json';proof=json.loads(p.read_text());assert all(sha(q)==h for q,h in proof['bindings'].items());bindings.update(proof['bindings']);bindings[str(p)]=sha(p)
O=R/'experiments/criticality_feedback_driver_qualification_v1_2026-10-10';O.mkdir();diff=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str(old),tofile=str(new)));(O/'source.diff').write_text(diff);bindings[str(O/'source.diff')]=sha(O/'source.diff')
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,initial_floor_raw_budget_path_body_exactly_preserved=True,overflow_rejection_commit_epoch_context_finish_body_exactly_preserved=True,criticality_core_contract_bindings_current=True,scope='Pre-run source lineage only. Full new trajectory and independent XML/objective transaction audit required; not production correctness or performance proof.'),indent=2)+'\n');print('CRITICALITY FEEDBACK SOURCE QUALIFICATION PASS')
