"""Count actual expand invocations across fanout, congestion and early-stop cases."""
import copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from criticality_shared_tree_sparse_reference_v3 import Graph
from criticality_retained_net_primary_v1 import route
from source_binding_v2 import closure
from pre_route_endpoints import sha

class TracedGraph(Graph):
 def tree(self,source):
  tree=super().tree(source);original=tree.expand;self.trace=[]
  def traced(target,*args):
   self.trace.append(target-1)
   return original(target,*args)
  tree.expand=traced
  return tree

def run(n,dirty,root_overused=False,fail=None):
 graph=TracedGraph(dict(row_offsets=[0]+[n]*(n+1),dest_ranks=list(range(1,n+1))),[1]*n,[0]*(n+1))
 qs=[dict(connection_id=i,net_id=7,source=0,sink=i+1) for i in range(n)]
 old=[dict(q,budget_integer=0 if q['connection_id']==fail else 1,answer=dict(physical_edge_ids=[100+q['connection_id']])) for q in qs]
 criticalities={i:dict(net=7,source_rr=0,target_rr=i+1,local_sink_pin=i+1,criticality_numerator=n-i,criticality_denominator=n) for i in range(n)}
 ledger={i:1 for i in range(n+1)};ledger.update({i+1:2 for i in dirty})
 if root_overused:ledger[0]=2
 before=copy.deepcopy((old,ledger))
 result=route(graph,qs,old,criticalities,{},list(range(100,100+n)),ledger,[1]*(n+1),{100+i:i for i in range(n)})
 expected_kept=[] if n<16 or root_overused else [i for i in range(n) if i not in dirty]
 expected_calls=[i for i in range(n) if i not in expected_kept]
 if fail is not None:expected_calls=expected_calls[:expected_calls.index(fail)+1]
 assert result['retained_connection_ids']==expected_kept
 assert graph.trace==expected_calls
 assert result['search_calls']==len(graph.trace)
 assert [r['connection_id'] for r in result['search_results'] if r['status']!='RETAINED_CLEAN_BRANCH']==graph.trace
 assert result['complete']==(fail is None)
 assert (old,ledger)==before
 return dict(fanout=n,dirty_connections=sorted(dirty),root_overused=root_overused,failed_connection=fail,actual_expand_trace=graph.trace,retained=expected_kept)

if __name__=='__main__':
 bindings=closure([Path(__file__)])
 rows=[run(15,set()),run(16,set()),run(17,{2,7}),run(16,set(range(16))),run(16,set(),True),run(16,{2,7},fail=2),run(16,{2,7},fail=7),run(15,{2},fail=2)]
 assert all(sha(p)==h for p,h in bindings.items())
 out=Path(__file__).resolve().parents[1]/'experiments/mmc_selective_tree_preflight_v1_2026-10-13/primary_call_trace_verification_v1.json'
 with out.open('x') as f:json.dump(dict(bindings=bindings,cases=rows,actual_expand_calls_match_reported_counts=True,scope='Eight small deterministic fixtures; no execution trace of full MMC run and no timing speedup claim.'),f,indent=2)
 print('PASS: eight actual expand traces, fanout boundary, congestion, early stop and input immutability')
