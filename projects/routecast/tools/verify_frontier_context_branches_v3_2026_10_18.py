"""Shared graph freeze, path-check parity and separate branch token ownership."""
import copy,json,sys
from dataclasses import FrozenInstanceError
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from retained_tree_frontier_state_v2 import Cache as Old
from retained_tree_frontier_state_v3 import Cache,GraphContext

def main():
 out=R/'experiments/frontier_context_branches_v3_2026-10-18';out.mkdir(exist_ok=False);kinds=['SOURCE','OPIN','CHANX','CHANY','CHANX','IPIN','SINK','IPIN','SINK'];geo={n:[k,n,n,0,0,0] for n,k in enumerate(kinds)};edges=frozenset([(0,1),(1,2),(1,3),(2,4),(3,4),(4,5),(5,6),(4,7),(7,8)]);original={0:(0,1,2,4,5,6),1:(0,1,2,4,7,8)};alternate={0:(0,1,3,4,5,6),1:(0,1,3,4,7,8)};records=[dict(connection_id=c,net_id=0,source=0,sink=p[-1],path=list(p)) for c,p in original.items()];calls=[]
 def checker(a,b):calls.append((a,b));return (a,b) in edges
 legacy=Old('g',geo,records,checker);legacy_calls=len(calls);context=GraphContext('g',geo,checker);assert len(calls)==legacy_calls;source=Cache(context,records);assert len(calls)-legacy_calls==legacy_calls;second=Cache(context,records);assert source._geometry is second._geometry is context.geometry and source._state is not second._state and source.view().snapshot()==legacy.view().snapshot()==second.view().snapshot();saved=source.view().snapshot();source_view=source.view();before_checks=len(calls);parent_ticket=source.prepare('g',0,[0]);branch=source.branch('g',0);assert len(calls)==before_checks and branch._state is source._state and not branch._pending and branch.view().snapshot()==saved
 rejected=[]
 def reject(name,fn):
  try:fn()
  except ValueError:rejected.append(name)
  else:raise AssertionError(name)
 reject('branch_cannot_commit_parent_ticket',lambda:branch.commit(parent_ticket));child_ticket=branch.prepare_paths('g',0,alternate);reject('parent_cannot_commit_child_ticket',lambda:source.commit(child_ticket));source.commit(parent_ticket);branch.commit(child_ticket);assert source.view().query(0)['path'] is None and source.view().query(1)['path']==original[1];assert all(branch.view().query(c)['path']==p for c,p in alternate.items());assert source_view.snapshot()==second.view().snapshot()==saved;assert source._geometry is branch._geometry is context.geometry;reject('stale_branch_generation',lambda:source.branch('g',0));reject('foreign_graph_branch',lambda:source.branch('foreign',1))
 old_geo=context.geometry[4];geo[4][1]=999;records[0]['path'].clear();assert context.geometry[4]==old_geo and source_view.snapshot()==saved
 try:context.epoch='changed'
 except FrozenInstanceError:rejected.append('context_field_immutable')
 else:raise AssertionError('context mutation')
 try:context.geometry[4]=('CHANX',0,0,0,0,0)
 except TypeError:rejected.append('geometry_mapping_immutable')
 else:raise AssertionError('geometry mutation')
 reject('bad_context',lambda:Cache(object(),[]));bad=copy.deepcopy(records);bad[0]['path']=[0,3,4,5,6];reject('new_source_paths_still_checked',lambda:Cache(context,bad));assert source_view.snapshot()==saved
 bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/retained_tree_frontier_state_v3.py',R/'tools/retained_tree_frontier_state_v2.py',R/'tools/retained_tree_frontier_state_v1.py',R/'tools/incremental_IPIN_feature_cache_v1.py']}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='shared_graph_freeze_edge_admission_parity_and_branch_owner_isolation_pass',bindings=bindings,initial_source_edge_checks=legacy_calls,branch_initial_edge_checks=0,rejected=rejected,scope='Separate serial cache owners share immutable graph and already-published source state only. No inter-thread synchronization, raw counter import, durable storage or native integration.'),f,indent=2)
 print('GRAPH CONTEXT AND BRANCH ISOLATION PASS',len(rejected),flush=True)
if __name__=='__main__':main()
