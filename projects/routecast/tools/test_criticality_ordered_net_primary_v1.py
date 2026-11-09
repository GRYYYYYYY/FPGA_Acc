import json,copy
from pathlib import Path
from criticality_shared_tree_sparse_reference_v2 import Graph
from criticality_ordered_net_primary_v1 import route
from pre_route_endpoints import sha
f=dict(row_offsets=[0,2,3,4,4],dest_ranks=[1,2,3,1]);inc=[10,1,1,1];graph=Graph(f,inc,[0]*4)
qs=[dict(connection_id=0,net_id=9,source=0,sink=1),dict(connection_id=1,net_id=9,source=0,sink=3)]
old=[dict(q,budget_integer=20 if q['sink']==1 else 4,answer=dict(physical_edge_ids=[1,3] if q['sink']==1 else [1,3,2],delay=2 if q['sink']==1 else 3)) for q in qs]
c={q['connection_id']:dict(net=9,source_rr=0,target_rr=q['sink'],local_sink_pin=q['connection_id']+1,criticality_numerator=1,criticality_denominator=4) for q in qs}
frozen=copy.deepcopy((qs,old,c));result=route(graph,qs,old,c,{2:100},list(range(4)))
assert result['order']==[0,1] and not result['complete'] and result['first_failed_connection_id']==1
assert result['attempts'][0]['physical_edge_ids']==[0] and result['attempts'][1]['physical_edge_ids']==[0,2]
assert result['search_results'][1]['raw']==11 and (qs,old,c)==frozen
bad=copy.deepcopy(c);bad[0]['net']=10
try:route(graph,qs,old,bad,{2:100},list(range(4)))
except ValueError:pass
else:raise AssertionError('wrong NET admitted')
# Increasing sink3 criticality changes order and establishes fast shared tree.
c[1]['criticality_numerator']=1;c[1]['criticality_denominator']=1
result=route(graph,qs,old,c,{2:100},list(range(4)));assert result['order']==[1,0] and result['complete']
assert [r['raw'] for r in result['search_results']]==[3,2]
out=Path('experiments/criticality_ordered_net_primary_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve()]+[Path('tools')/x for x in ['criticality_ordered_net_primary_v1.py','criticality_shared_tree_sparse_reference_v2.py']]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p.resolve()):sha(p) for p in files},ordering_and_budget_attempt_paths_and_identity_rejection_pass=True,scope='Concrete two-pin order-sensitive boundary only; random and real full-NET coverage remain open.'),indent=2)+'\n');print('ORDERED NET PRIMARY BOUNDARY PASS')
