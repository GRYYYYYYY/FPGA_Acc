"""Borrowed-tree read-only checks and unchanged initializer success/fallback/errors."""
import copy,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from compiled_criticality_tree_v1 import Graph,BINARY
from retained_criticality_tree_seed_v1 import seed
from retained_tree_frontier_state_v3 import GraphContext
from borrowed_compiled_frontier_v1 import Probe
from native_retained_net_initializer_v1 import initialize as old
from native_retained_net_initializer_observed_v2 import initialize as observed,ObservationError
from pre_route_endpoints import sha

def main():
 out=R/'experiments/borrowed_compiled_frontier_core_v1_2026-10-18';out.mkdir(exist_ok=False);rows=[]
 fixtures=[
  ('success',dict(row_offsets=[0,2,4,4,4],dest_ranks=[1,3,2,3],edge_ids=list(range(4)),capacities=[1]*4),[10,3,1,10],[0,2],[0,2],3,False),
  ('bad_fallback_budget',dict(row_offsets=[0,2,4,4,4],dest_ranks=[1,3,2,3],edge_ids=list(range(4)),capacities=[1]*4),[10,3,1,10],[0,2],[0,2],2,True),
  ('disabled_raw_shortcut',dict(row_offsets=[0,3,5,5,5],dest_ranks=[1,2,3,2,3],edge_ids=list(range(5)),capacities=[1,0,1,1]),[1,4,9,1,1],[1],[1],9,False)]
 for name,f,inc,path0,path1,budget,error_expected in fixtures:
  g=Graph(f,inc,[0]*4);kinds=['SOURCE','CHANX','SINK','SINK'];geo={n:(kind,n,n,0,0,0) for n,kind in enumerate(kinds)};context=GraphContext('graph',geo,lambda a,b:any(g.dest[j]==b for j in range(g.offsets[a],g.offsets[a+1])));probe=Probe(g,context);oldrows=[dict(connection_id=0,net_id=0,source=0,sink=2,answer=dict(status='FOUND',physical_edge_ids=path0,delay=sum(inc[i] for i in path0))),dict(connection_id=1,net_id=0,source=0,sink=2,answer=dict(status='FOUND',physical_edge_ids=path1,delay=sum(inc[i] for i in path1)))];queries=[dict(connection_id=0,net_id=0,source=0,sink=2),dict(connection_id=1,net_id=0,source=0,sink=3)];budgets={0:oldrows[0]['answer']['delay'],1:budget};fallback_paths={0:path0,1:[1] if name!='disabled_raw_shortcut' else [2]};source=copy.deepcopy(oldrows);events=[];calls=[]
  def fallback():
   calls.append(1);return {c:dict(status='FOUND',physical_edge_ids=p,delay=sum(inc[i] for i in p)) for c,p in fallback_paths.items()}
  def run(fn,enabled):
   before=tuple(g.total_stats);calls.clear()
   try:value=fn(g,f,kinds,queries,oldrows,budgets,range(len(inc)),fallback,**(dict(frontier_probe=probe,emit=lambda e:events.append(dict(e))) if enabled else {}));result=('return',value)
   except ValueError as e:result=('error',type(e).__name__,str(e))
   return result,tuple(a-b for a,b in zip(g.total_stats,before)),len(calls)
  a=run(old,False);b=run(observed,True);assert a==b and oldrows==source and len(events)==2 and (a[0][0]=='error')==error_expected;assert events[0]['actual_seed_nodes']>events[0]['projected_expandable_nodes']
  if name=='disabled_raw_shortcut':assert a[0][1]['whole_NET_fallback'] and events[-1]['expand_committed'] is True
  if name=='bad_fallback_budget':assert events[-1]['expand_committed'] is False and events[0]['actual_seed_nodes']==events[-1]['actual_seed_nodes']
  t=g.tree(0);seed(t,[(2,path0,budgets[0])]);snapshot=(dict(t.parents),dict(t.arrival),tuple(g.total_stats),g.last_stats);capture=probe.capture(t,3);assert snapshot==(t.parents,t.arrival,tuple(g.total_stats),g.last_stats)
  calls.clear()
  def broken(event):raise ValueError('observer failure fixture')
  try:observed(g,f,kinds,queries,oldrows,budgets,range(len(inc)),fallback,frontier_probe=probe,emit=broken)
  except ObservationError:pass
  else:raise AssertionError('observation error hidden as routing fallback')
  assert not calls and oldrows==source
  rows.append(dict(fixture=name,baseline_observed_exact=True,events=events,compiled_stats=a[1],fallback_calls=a[2],observability_error_did_not_invoke_fallback=True,borrow_capture_did_not_mutate_tree_or_backend=True));g.close()
  try:probe.capture(t,3)
  except ValueError:pass
  else:raise AssertionError('closed graph probe accepted')
 # No-repair case: observer remains silent and source answers unchanged.
 f=fixtures[0][1];g=Graph(f,fixtures[0][2],[0]*4);geo={n:(k,n,n,0,0,0) for n,k in enumerate(['SOURCE','CHANX','SINK','SINK'])};probe=Probe(g,GraphContext('g',geo,lambda a,b:True));q=[dict(connection_id=0,net_id=0,source=0,sink=2)];o=[dict(q[0],answer=dict(status='FOUND',physical_edge_ids=[0,2],delay=11))];events=[];fb=lambda:(_ for _ in ()).throw(AssertionError('unexpected fallback'));assert old(g,f,['SOURCE','CHANX','SINK','SINK'],q,o,{0:11},range(4),fb)==observed(g,f,['SOURCE','CHANX','SINK','SINK'],q,o,{0:11},range(4),fb,frontier_probe=probe,emit=lambda e:events.append(e));assert events==[];g.close()
 bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/borrowed_compiled_frontier_v1.py',R/'tools/native_retained_net_initializer_observed_v2.py',R/'tools/native_retained_net_initializer_v1.py',R/'tools/retained_tree_frontier_state_v3.py',R/'tools/compiled_criticality_tree_v1.py',R/'tools/retained_criticality_tree_seed_v1.py',R/'tools/raw_retained_tree_expand_v1.py',BINARY]}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='borrowed_tree_read_only_and_initializer_output_stats_fallback_parity_pass',bindings=bindings,rows=rows,no_repair_observer_events=0,scope='Observer sees existing compiled arrival seeds and separate type-filtered projection. Raw expand commit is not wholeNET or legal-route admission. Real producer validation and full-flow timing pending.'),f,indent=2)
 print('BORROWED FRONTIER CORE PASS',len(rows),flush=True)
if __name__=='__main__':main()
