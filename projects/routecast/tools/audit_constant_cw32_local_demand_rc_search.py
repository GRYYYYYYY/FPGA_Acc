"""Full frozen-cohort exact lattice parity with independent Fraction search."""
import json,time,shutil
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from prepared_csr import read,U64
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from native_integer_rc_sink_bound import NativeIntegerRCSinkBound
from local_other_demand import LocalOtherDemand
from rc_feasible_cost_region import RCFeasibleCostRegion
from csr_integer_sink_bound_search import query as pruned_query
from verify_rc_remaining_certificate import verify as verify_bounds
from csr_integer_budget_search import query
from pre_route_endpoints import sha

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/constant_multiplier_cw32_local_demand_parity_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('audit_constant_cw32_local_demand_rc_search.py','local_other_demand.py','native_integer_rc_delta_search.py','native_integer_rc_sink_bound.py','rc_feasible_cost_region.py','csr_integer_sink_bound_search.py','verify_rc_remaining_certificate.py','native_integer_rc_search.py','integer_rc_context.py','csr_integer_budget_search.py','csr_exact_buffered_rc.py','prepared_csr.py','buffered_rc_context.py','buffered_rc_node_classes.py','pre_route_endpoints.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'cpp_source_sha256':sha(root/'tools/rc_budget_native_sink_bound/search.cpp'),'native_binary_sha256':sha(root/'build/rc_budget_native_sink_bound_2026-10-06/search.so'),'cohort':[f'mult_{i:03d}' for i in range(1,7)],'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'Native pruned results equal independent Python pruned results including counters; archived Fraction status/path/objective/delay and serial overflow admission also match. Pruned resource policy intentionally differs in general. All sink distances independently certified. Native transport uint64 and arithmetic uint128 restrictions retained; no hardware claim. One execution wall time, no paired performance gain claim.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');reports=[];bindings={}
 for name in protocol['cohort']:
  for folder in ('constant_multiplier_cw32_rc_budgeted_nets_2026-10-06','constant_multiplier_family_predictions_cw32_2026-10-06','constant_multiplier_cw32_exact_buffered_rc_classes_2026-10-06','constant_multiplier_family_length_switch_csr_cw32_2026-10-06'):
   for path in (root/'experiments'/folder/name).rglob('*'):
    if path.is_file():bindings[str(path)]=sha(path)
  start=time.monotonic();dest=out/name;dest.mkdir();parent=root/'experiments/constant_multiplier_cw32_rc_budgeted_nets_2026-10-06'/name;prior=json.loads((parent/'receipt.json').read_text());assert sha(parent/'queries.jsonl')==prior['queries_sha256'];truth={r['connection_id']:r['result'] for r in map(json.loads,(parent/'queries.jsonl').read_text().splitlines())};baseline=root/'experiments/constant_multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset';pred=json.loads((baseline/'prediction.json').read_text());context=root/'experiments/constant_multiplier_cw32_exact_buffered_rc_classes_2026-10-06'/name;budgets={r['connection_id']:Fraction(*r['exact_delay_s']) for r in json.loads((context/'baseline_budgets.json').read_text())};m,f=read(root/'experiments/constant_multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',pred['physical_graph_sha256']);rc=ExactBufferedRC(f,*load(context,pred['physical_graph_sha256']));t=time.monotonic();integer=IntegerRC(rc);native=NativeIntegerRCSinkBound(integer);region=RCFeasibleCostRegion(m['nodes'],[(u,f['dest_ranks'][i],integer.increments[i],f['costs'][i]) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0]);certified={};local=LocalOtherDemand(native);dirty=set();examined_nodes=0;writes=0;epochs=0;accepted=0;rejected=0;init_s=time.monotonic()-t;groups=defaultdict(list);edge={f['edge_ids'][i]:(n,f['dest_ranks'][i]) for n in range(m['nodes']) for i in range(f['row_offsets'][n],f['row_offsets'][n+1])}
  for r in pred['connections']:groups[r['net_id']].append(r)
  def union(rows):
   nodes=set()
   for r in rows:
    nodes.add(r['source'])
    for e in r['physical_edge_ids']:nodes.update(edge[e])
   return nodes
  unions={n:union(rows) for n,rows in groups.items()};occ=Counter(n for nodes in unions.values() for n in nodes);overflow=lambda values:sum(max(0,v-f['capacities'][n]) for n,v in values.items());checked=0;t=time.monotonic()
  for net,rows in sorted(groups.items()):
   other=occ.copy();other.subtract(unions[net]);count,inspected=local.transition(occ,unions[net],dirty);writes+=count;examined_nodes+=inspected;epochs+=1;dirty=set();assert local.values==dict(+other);assert set(native.previous)==set(+other);assert all(int(native.other[n])==other.get(n,0) for n in range(m['nodes']));candidate=[]
   for r in rows:
    remaining=region.distance(r['sink'],True)
    if r['sink'] not in certified:
     certified[r['sink']]=verify_bounds(f,integer.increments,r['sink'],[remaining.get(n,U64) for n in range(m['nodes'])])
    budget=integer.encode(budgets[r['connection_id']]);result=native.query_bound(r['source'],r['sink'],budget,remaining,10000)
    oracle=pruned_query(integer,r['source'],r['sink'],budget,lambda u,i:f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0,lambda u,i:int(f['costs'][i])*(1+other[f['dest_ranks'][i]]),remaining,10000)
    assert result==oracle
    old=truth[r['connection_id']];assert result['status']==old['status'] and result['physical_edge_ids']==old['physical_edge_ids'] and result['cost']==old['cost'];assert Fraction(result['delay'],integer.scale)==Fraction(old['delay']);candidate.append({**r,'physical_edge_ids':result['physical_edge_ids']});checked+=1
   staged=other.copy();newunion=union(candidate);staged.update(newunion)
   if overflow(staged)<=overflow(occ):
    dirty=unions[net]^newunion;occ=staged;unions[net]=newunion;accepted+=1
   else:rejected+=1
  report={'design':name,'full_buffer_and_active_set_verified_every_net_epoch':True,'net_epochs':epochs,'accepted_nets':accepted,'rejected_nets':rejected,'demand_candidates_examined':examined_nodes,'demand_nodes_written':writes,'certified_sinks':len(certified),'all_pruned_results_equal_python_including_counters':True,'queries_exact_same_path_cost_delay':checked,'final_overflow':overflow(occ),'scale_bits':integer.scale.bit_length(),'context_conversion_s':init_s,'search_and_state_s':time.monotonic()-t,'driver_wall_s':time.monotonic()-start};assert report['final_overflow']==prior['final_overflow'];reports.append(report);print(json.dumps(report),flush=True)
 assert sha(root/'tools/rc_budget_native_sink_bound/search.cpp')==protocol['cpp_source_sha256'] and sha(root/'build/rc_budget_native_sink_bound_2026-10-06/search.so')==protocol['native_binary_sha256']
 assert all(sha(Path(n))==h for n,h in bindings.items())
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'inputs_sha256':bindings,'results':reports},indent=2)+'\n')
if __name__=='__main__':main()
