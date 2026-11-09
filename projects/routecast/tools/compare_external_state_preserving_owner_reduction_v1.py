"""Replay one archived SAT model, only change deterministic surplus deletion order."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from state_preserving_owner_reduction_v1 import reduce_witness
from verify_certified_cnf_dependency_cdcl_v1 import verify
from zero_rc_budget_certificate_graph_v1 import load_graph,candidate_nodes
from cut_owner_actor_requirements_v1 import required_actors
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prospective_external_family_budget_closed_pure_batch_ownership_v1_2026-10-19';H=E/'prospective_external_family_joint_cut_owner_replacement_v1_2026-10-19';O=E/'prospective_external_family_state_preserving_owner_reduction_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 O.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);paths=[S/'verification.json',S/'physical_proposal_preflight_v1.json',E/'state_preserving_owner_reduction_contract_v1_2026-10-19/verification.json'];coverage={}
 for name in ['all_CID_terminal_budget_domains','actor_CID_domain_expansion','batched_actor_CID_domain_expansion','budget_closure_frontier_CID_domains']:
  p=E/f'prospective_external_family_{name}_v1_2026-10-19/independent_verification_v1.json';paths.append(p)
  for r in read(p)['rows']:
   assert r['all_original_CIDs_covered'];coverage.setdefault(r['case'],set()).add(r['NET'])
 for p in paths:
  d=read(p);assert all(sha(q)==h for q,h in d['bindings'].items());bindings[str(p)]=sha(p)
 graph=next(Path(p) for p in read(paths[-1])['bindings'] if p.endswith('/rr_graph.xml'));g=load_graph(graph);bindings[str(graph)]=sha(graph);prior={r['case']:r for r in read(S/'physical_proposal_preflight_v1.json')['rows']};rows=[]
 for spec in read(S/'protocol.json')['cases']:
  case=spec['case'];directory=O/case;directory.mkdir(parents=True);ep=S/case/'encoding.json';rp=S/case/'result.json';fp=H/case/'final_conditional_trees.jsonl';cnf=read(ep);raw=read(rp);verify(cnf['clauses'],raw);assert raw['status']=='SAT';state={r['net_id']:candidate_nodes(r['candidate'],g['vs']) for r in map(json.loads,fp.read_text().splitlines())};model={int(k):v for k,v in raw['model'].items()};active=[(v['node'],v['NET']) for i,v in enumerate(cnf['variables'],1) if model[i]];reduced=reduce_witness(active,spec['cuts'],state);chosen=set(map(tuple,reduced['active']));new_model={i:(v['node'],v['NET']) in chosen for i,v in enumerate(cnf['variables'],1)};verify(cnf['clauses'],dict(status='SAT',model=new_model,rup_additions=[]))
  # Independently replay coverage and each single-deletion witness.
  for c in spec['cuts']:assert {(n,c['NET']) for n in c['nodes']}&chosen
  for n,net in chosen:assert any({(v,c['NET']) for v in c['nodes']}&chosen=={(n,net)} for c in spec['cuts'])
  allocation=dict(chosen);req=required_actors(allocation,state,coverage[case]);old=prior[case]['requirements']['required_actor_NETs'];row=dict(case=case,status='SAT',prior_actor_NETs=old,required_actor_NETs=req['required_actor_NETs'],actors_missing_all_CID_domain_proofs=req['actors_missing_all_CID_domain_proofs'],actor_count_change=len(req['required_actor_NETs'])-len(old),one_logical_owner_allocation=[dict(node=n,required_owner_NET=net,current_owner_NETs=sorted(t for t,ns in state.items() if n in ns)) for n,net in sorted(chosen)],route_feasibility_proved=False);rows.append(row);out=directory/'reduced_model.json';out.write_text(json.dumps(dict(reduction=reduced,model=new_model),indent=2)+'\n')
  for p in (ep,rp,fp,out):bindings[str(p)]=sha(p)
  print('STATE_PRESERVING_REDUCTION',json.dumps({k:v for k,v in row.items() if k!='one_logical_owner_allocation'}),flush=True)
 p=S/'protocol.json';bindings[str(p)]=sha(p);assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(status='ALL3_STATE_PRESERVING_SUBSETS_OF_ARCHIVED_MODELS_INDEPENDENTLY_CHECKED',rows=rows,bindings=bindings,scope='Original archived clauses only, no new SAT search. Newly derived frontier cuts are coverage evidence, NOT included in these old CNFs. A subsequent cumulative solve must admit them. Local subset selection, not global minimum actor count, tree feasibility or quality/utility success.'),indent=2)+'\n')
if __name__=='__main__':main()
