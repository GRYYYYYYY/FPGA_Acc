"""One fixed certified solve of accumulated graph-proved cut ownership conditions."""
import json,sys,itertools,time
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from conditional_package_tree_search_v1 import owned
from conditional_budget_cut_admission_v2 import verified_store,admit
from irredundant_cut_owner_witness_v1 import reduce_witness
from budget_cut_ownership_relaxation_v1 import encode
from certified_cnf_dependency_cdcl_v2 import solve
from verify_certified_cnf_dependency_cdcl_v1 import verify
R=Path(__file__).resolve().parents[1];E=R/'experiments';A=E/'prospective_external_family_budget_resource_cuts_v1_2026-10-19';C=E/'prospective_external_family_additional_budget_resource_cuts_v1_2026-10-19';T=E/'prospective_external_family_all_CID_terminal_budget_domains_v1_2026-10-19';H=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';O=E/'prospective_external_family_all_CID_accumulated_ownership_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);clauses=[]
 for directory in (A,C,T):
  artifact=directory/'learned_conditional_budget_constraints_v1.json';proof=directory/'independent_verification_v1.json';clauses.extend(verified_store(artifact,proof));bindings[str(artifact)]=sha(artifact);bindings[str(proof)]=sha(proof)
 for p in (E/'irredundant_cut_owner_witness_contract_v1_2026-10-19/verification.json',E/'conditional_budget_cut_admission_contract_v2_2026-10-19/verification.json'):
  proof=read(p);assert all(sha(q)==h for q,h in proof['bindings'].items());bindings[str(p)]=sha(p)
 contract=E/'budget_cut_ownership_relaxation_contract_v1_2026-10-19/verification.json';r=read(contract);assert r['status']=='CUT_OWNERSHIP_RELAXATION_EQUALS_EXHAUSTIVE_OWNER_FUNCTIONS_WITH_CERTIFIED_SOLVES';assert all(sha(p)==h for p,h in r['bindings'].items());bindings[str(contract)]=sha(contract);matrix=E/'prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';inputs={r['case']:r for r in read(matrix)['rows']};_,digest,nodes,fields,rc,_=load_endpoints(inputs['w160/episode_01']['endpoint']);slots={e:i for i,e in enumerate(fields['edge_ids'])};bindings[str(matrix)]=sha(matrix);cases=[];data={}
 for prior in read(H/'protocol.json')['cases']:
  case=prior['case'];bp=B/case/'candidate_bank.jsonl';fp=H/case/'final_conditional_trees.jsonl';bank={r['net_id']:r['candidates'] for r in map(json.loads,bp.read_text().splitlines())};state={r['net_id']:r['candidate'] for r in map(json.loads,fp.read_text().splitlines())};package=set(prior['package_NETs']);outside=Counter()
  for net,options in bank.items():
   if net not in package:outside.update(set.intersection(*(owned(c,fields,slots) for c in options)))
  admitted=[]
  for clause in clauses:
   if clause['case']!=case:continue
   q=next(r for r in bank[clause['NET']][0]['records'] if r['connection_id']==clause['connection_id']);admit(clause,case,digest,q,outside);assert all(fields['capacities'][n]==1 and outside[n]==0 for n in clause['conditional_budget_cut']);admitted.append(clause)
  assert admitted;spec=dict(case=case,cuts=[dict(NET=c['NET'],CID=c['connection_id'],nodes=c['conditional_budget_cut'],necessity_certificate=c.get('negative_certificate_query') or c['necessity_certificate']) for c in admitted]);cases.append(spec);data[case]={net:owned(c,fields,slots) for net,c in state.items()}
  for p in (bp,fp):bindings[str(p)]=sha(p)
 p=H/'protocol.json';bindings[str(p)]=sha(p);policy='Exactly one solve per fixed case, max1000 nodes, no work-bound or assignment sweep. Every admitted graph-proved cut requires its NET to own at least one cut resource; every unit resource at most one NET owner. Multiple cuts for the same NET may share an owner resource. This is a necessary ownership relaxation only. SAT is directly checked against original cuts and capacity, UNSAT needs RUP. Independently rebuild all variables/clauses and exhaustively enumerate owner functions when assignments<=1000000, otherwise report that check unavailable. For a SAT result deterministically delete surplus true owners in descending(node,NET) order while preserving every original cut; do not search another model. Independently verify the reduced assignment satisfies the original CNF and each retained owner uniquely satisfies at least one cut. No tree search or native mutation. Attribution baseline is the prior final/restored state; graph-cut derivation never substitutes it for the actual failure search mask.'
 (O/'protocol.json').write_text(json.dumps(dict(policy=policy,cases=cases,bindings=bindings,unavailable_cases_preserved=6),indent=2)+'\n');rows=[]
 for spec in cases:
  case=spec['case'];directory=O/case;directory.mkdir(parents=True);cnf=encode(spec['cuts']);pairs=sorted({(n,c['NET']) for c in spec['cuts'] for n in c['nodes']});assert cnf['variables']==[dict(kind='OWNER',node=n,NET=net) for n,net in pairs];roles={(v['node'],v['NET']):i for i,v in enumerate(cnf['variables'],1)};expected={tuple(sorted(roles[n,c['NET']] for n in set(c['nodes']))) for c in spec['cuts']}
  for n in sorted({p[0] for p in pairs}):
   variables=sorted(roles[p] for p in pairs if p[0]==n)
   for i,v in enumerate(variables):
    for w in variables[i+1:]:expected.add(tuple(sorted((-v,-w))))
  assert cnf['clauses']==[list(c) for c in sorted(expected)];ep=directory/'encoding.json';ep.write_text(json.dumps(cnf,indent=2)+'\n');start=time.perf_counter();result=solve(cnf['clauses'],len(cnf['variables']),max_nodes=1000);elapsed=time.perf_counter()-start;verify(cnf['clauses'],result);rp=directory/'result.json';rp.write_text(json.dumps(result,indent=2)+'\n');truth=None;count=0;resource_nodes=sorted({n for n,net in pairs});eligible={n:sorted({net for node,net in pairs if node==n}) for n in resource_nodes};assignment_count=1
  for n in resource_nodes:assignment_count*=len(eligible[n])+1
  if assignment_count<=1000000:
   truth=False
   for values in itertools.product(*([None]+eligible[n] for n in resource_nodes)):
    allocation=dict(zip(resource_nodes,values));expected_truth=all(any(allocation[n]==cut['NET'] for n in cut['nodes']) for cut in spec['cuts']);model={i:allocation[v['node']]==v['NET'] for i,v in enumerate(cnf['variables'],1)};actual=all(any(model[abs(lit)]==(lit>0) for lit in clause) for clause in cnf['clauses']);assert actual==expected_truth;truth|=expected_truth;count+=1
   if result['status']!='UNKNOWN_SEARCH_LIMIT':assert truth==(result['status']=='SAT')
  allocations=[]
  if result['status']=='SAT':
   model={int(k):v for k,v in result['model'].items()};raw_active=[(v['node'],v['NET']) for i,v in enumerate(cnf['variables'],1) if model[i]];reduced=reduce_witness(raw_active,spec['cuts']);active=list(map(tuple,reduced['active']));active_set=set(active);reduced_model={i:(v['node'],v['NET']) in active_set for i,v in enumerate(cnf['variables'],1)};verify(cnf['clauses'],dict(status='SAT',model=reduced_model,rup_additions=[]));assert len({n for n,net in active})==len(active);assert all(any((n,c['NET']) in active for n in c['nodes']) for c in spec['cuts'])
   for witness in reduced['irreducibility_witnesses']:
    assert witness['unique_owner_cut_indices'] and all({(n,c['NET']) for n in c['nodes']}&active_set=={(witness['node'],witness['NET'])} for c in [spec['cuts'][i] for i in witness['unique_owner_cut_indices']])
   reduced_path=directory/'irredundant_owner_model.json';reduced_path.write_text(json.dumps(dict(reduction=reduced,model=reduced_model),indent=2)+'\n');bindings[str(reduced_path)]=sha(reduced_path);current=data[case]
   for n,net in active:allocations.append(dict(node=n,required_owner_NET=net,current_owner_NETs=sorted(owner for owner,ns in current.items() if n in ns),current_conflicting_NETs=sorted(owner for owner,ns in current.items() if owner!=net and n in ns)))
  row=dict(case=case,status=result['status'],visited_nodes=result['visited_nodes'],cuts=len(spec['cuts']),OWNER_variables=len(cnf['variables']),clauses=len(cnf['clauses']),independent_structure_exact=True,owner_function_assignments_checked=count,owner_function_truth=truth,certificate_or_model_verified=True,one_logical_owner_allocation=allocations,solver_component_seconds=elapsed,route_feasibility_proved=False);rows.append(row);(directory/'verification.json').write_text(json.dumps(row,indent=2)+'\n')
  for p in (ep,rp,directory/'verification.json'):bindings[str(p)]=sha(p)
  print('ACCUMULATED_CUT_OWNERSHIP',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(status='ALL3_ACCUMULATED_BUDGET_CUT_OWNERSHIP_RELAXATIONS_TERMINAL_VERIFIED',rows=rows,bindings={str(O/'protocol.json'):sha(O/'protocol.json'),**bindings},labels_opened=False,budgets_changed=False,unavailable_cases_preserved=6,scope='SAT only shows these necessary resource ownership conditions are mutually consistent, not physical path/tree construction, outside completion, ranking or utility gain. UNSAT would refute only the admitted fixed-outside budget assumptions. Reported logical allocation is an inclusion-minimal subset of one raw SAT model, not minimum cardinality, optimized routing, or individually mandatory owners.'),indent=2)+'\n')
if __name__=='__main__':main()
