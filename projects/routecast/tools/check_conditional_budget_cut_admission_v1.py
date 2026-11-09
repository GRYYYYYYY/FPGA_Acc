"""Real-case premise rejection and exhaustive disjunctive unit ownership checks."""
import json,sys,itertools,copy
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from conditional_package_tree_search_v1 import owned
from conditional_budget_cut_admission_v1 import verified_store,admit,evaluate,outside_hash,ContextMismatch
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'conditional_budget_cut_admission_contract_v1_2026-10-19';C=E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';H=E/'prospective_external_family_monotone_witness_package_v1_2026-10-19'
def main():
 D.mkdir(exist_ok=False);artifact=C/'learned_conditional_budget_constraints_v1.json';proof=C/'independent_verification_v1.json';clauses=verified_store(artifact,proof);matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in json.loads(matrix.read_text())['rows']};_,digest,nodes,fields,rc,_=load_endpoints(inputs['w160/episode_01']['endpoint']);slots={eid:i for i,eid in enumerate(fields['edge_ids'])};packages={r['case']:set(r['package_NETs']) for r in json.loads((H/'protocol.json').read_text())['cases']};rows=[];bindings={str(p):sha(p) for p in (Path(__file__).resolve(),R/'tools/conditional_budget_cut_admission_v1.py',artifact,proof,matrix,H/'protocol.json')};rejected=truthcases=0
 for clause in clauses:
  case=clause['case'];bp=B/case/'candidate_bank.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};outside=Counter()
  for net,options in bank.items():
   if net not in packages[case]:outside.update(set.intersection(*(owned(c,fields,slots) for c in options)))
  query=next(r for r in bank[clause['NET']][0]['records'] if r['connection_id']==clause['connection_id']);assert admit(clause,case,digest,query,outside)==clause
  for name in ('case','graph','connection','NET','source','sink','budget','outside'):
   q=dict(query);c=case;g=digest;o=Counter(outside)
   if name=='case':c=case+'_different'
   elif name=='graph':g='0'*64
   elif name=='outside':o[clause['conditional_budget_cut'][0]]+=1
   else:q[{'connection':'connection_id','NET':'net_id','source':'source','sink':'sink','budget':'budget_integer'}[name]]+=1
   try:admit(clause,c,g,q,o)
   except ContextMismatch as error:assert str(error)==name;rejected+=1
   else:raise AssertionError('mismatched premise admitted')
  o=Counter(outside);o[query['source']]=0;assert outside_hash(o)==outside_hash(outside);bad=dict(outside);bad[query['source']]=-1
  try:outside_hash(bad)
  except ValueError:rejected+=1
  else:raise AssertionError('negative occupancy admitted')
  cut=clause['conditional_budget_cut'];assert all(outside[n]==0 for n in cut);local=0
  for labels in itertools.product(range(3),repeat=len(cut)):
   ownership={clause['NET']:{n for n,x in zip(cut,labels) if x==1},-1:{n for n,x in zip(cut,labels) if x==2}};answer=evaluate(clause,ownership,outside);assert answer['satisfied']==any(x!=2 for x in labels);assert answer['available_nodes']==[n for n,x in zip(cut,labels) if x!=2];truthcases+=1;local+=1
  bindings[str(bp)]=sha(bp);rows.append(dict(case=case,valid_context_admitted=True,premise_and_negative_occupancy_rejections=9,exhaustive_free_self_other_ownership_cases=local))
 fake=D/'unbound_artifact.json';fake.write_text(artifact.read_text())
 try:verified_store(fake,proof)
 except ValueError:rejected+=1
 else:raise AssertionError('unbound artifact admitted')
 bindings[str(fake)]=sha(fake);assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='CONDITIONAL_BUDGET_CUT_ADMISSION_AND_DISJUNCTIVE_OWNERSHIP_CONTRACT_VERIFIED',bindings=bindings,rows=rows,rejections=rejected,ownership_truth_cases=truthcases,scope='Exact verified-artifact and proof-premise admission, target-own occupancy allowed, any one cut node available suffices for this necessary clause. Not proof of complete routing.'),indent=2)+'\n');print(dict(valid_contexts=len(rows),rejections=rejected,ownership_cases=truthcases),flush=True)
if __name__=='__main__':main()
