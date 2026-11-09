"""Save actual failed-search private state, not the restored post-abort state."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from conditional_package_tree_search_v1 import owned
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19';H=E/'prospective_external_family_clause_guided_root_replacement_v1_2026-10-19';B=E/'prospective_external_family_blocker_release_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=D/'independent_verification_v1.json';a=read(proof);assert all(sha(p)==h for p,h in a['bindings'].items());matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};_,digest,nodes,fields,rc,_=load_endpoints(inputs['w160/episode_01']['endpoint']);slots={eid:i for i,eid in enumerate(fields['edge_ids'])};bindings={**closure([Path(__file__)]),str(proof):sha(proof),str(D/'protocol.json'):sha(D/'protocol.json'),str(matrix):sha(matrix)};rows=[]
 for spec in read(D/'protocol.json')['cases']:
  case=spec['case'];pp=H/case/'final_conditional_trees.jsonl';bp=B/case/'candidate_bank.jsonl';out=D/case;rp=out/'result.json';gp=out/'generated_trees.jsonl';initial={r['net_id']:r['candidate'] for r in map(json.loads,pp.read_text().splitlines())};bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};result=read(rp);generated={r['call']:r for r in map(json.loads,gp.read_text().splitlines())};state={net:c for net,c in initial.items() if net not in spec['transaction_NETs']};failure=None
  for event in result['events']:
   if event['status'] in ('FAILED_TRANSACTION_ABORTED','FAILED'):failure=event;break
   assert event['call'] in generated;row=generated[event['call']];assert row['net_id']==event['net_id'];state[row['net_id']]=row['candidate']
  assert failure and failure['net_id'] not in state;outside=Counter()
  for net,options in bank.items():
   if net not in set(spec['package_NETs']):outside.update(set.intersection(*(owned(c,fields,slots) for c in options)))
  usage=Counter(n for c in state.values() for n in owned(c,fields,slots));exhausted={n for n,cap in enumerate(fields['capacities']) if outside[n]+usage[n]>=cap};extra=failure.get('extra_forbidden_nodes',[]);assert len(exhausted|set(extra))==failure['forbidden_nodes'];assert all(outside[n]+count<=fields['capacities'][n] for n,count in usage.items());snapshot=out/'failed_search_trees_v1.jsonl';assert not snapshot.exists()
  with snapshot.open('x') as f:
   for net,c in sorted(state.items()):f.write(json.dumps(dict(net_id=net,candidate=c),separators=(',',':'))+'\n')
  record=dict(case=case,failed_NET=failure['net_id'],phase=failure['phase'],source_call=failure['call'],failed_CIDs=failure['failed_CIDs'],active_NETs=sorted(state),failed_NET_absent=True,active_NET_count=len(state),graph_sha256=digest,extra_forbidden_nodes=extra,extra_not_physically_exhausted_nodes=sorted(set(extra)-exhausted),has_only_physical_capacity_mask=not bool(set(extra)-exhausted),restored_final_state_is_different=state!={r['net_id']:r['candidate'] for r in map(json.loads,(out/'final_conditional_trees.jsonl').read_text().splitlines())},snapshot=str(snapshot),scope='Actual pre-failure conditional search state. If extra_not_physically_exhausted_nodes is nonempty, negative cuts need those additional algorithmic assumptions; do not present them as capacity-only cuts.')
  p=out/'failed_search_context_v1.json';p.write_text(json.dumps(record,indent=2)+'\n');rows.append(record)
  for p in (pp,bp,rp,gp,snapshot,out/'failed_search_context_v1.json'):bindings[str(p)]=sha(p)
  print('ACTUAL_FAILURE_CONTEXT',json.dumps({k:record[k] for k in ('case','failed_NET','active_NET_count','has_only_physical_capacity_mask','restored_final_state_is_different')}),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'failed_search_contexts_verification_v1.json').write_text(json.dumps(dict(status='ALL3_ACTUAL_FAILED_SEARCH_PRIVATE_STATES_MATERIALIZED',rows=rows,bindings=bindings,scope='Replay of independently verified events, no new route generation or proof of wider infeasibility. Distinguishes failed private state from rollback-restored final state.'),indent=2)+'\n')
if __name__=='__main__':main()
