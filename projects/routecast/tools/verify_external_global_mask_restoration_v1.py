"""Non-vacuous local RUP proofs: apparently freed CHOICEs remain excluded."""
import json,hashlib
from pathlib import Path
from verify_certified_cnf_dependency_cdcl_v1 import verify
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_cnf_v1_2026-10-19';C=E/'prospective_external_family_global_mask_cnf_v1_2026-10-19';I=E/'prospective_external_family_global_release_inventory_v1_2026-10-19';O=E/'prospective_external_family_global_mask_restoration_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def unit_roles(c):return {tuple(c['variables'][-clause[0]-1]['key']) for clause in c['clauses'] if len(clause)==1 and clause[0]<0 and c['variables'][-clause[0]-1]['kind']=='CHOICE'}
def main():
 proof=C/'independent_structure_verification_v1.json';p=read(proof);assert all(sha(q)==h for q,h in p['bindings'].items());O.mkdir(exist_ok=False);rows=[];bindings={str(q):sha(q) for q in (proof,Path(__file__).resolve(),R/'tools/verify_certified_cnf_dependency_cdcl_v1.py')}
 for ep in range(1,4):
  case=f'w160/episode_{ep:02d}';op=B/case/'encoding.json';np=C/case/'encoding.json';ip=I/f'episode_{ep:02d}.json';old=read(op);new=read(np);inventory=read(ip);before=unit_roles(old);after=unit_roles(new);freed=sorted(before-after);oldchoices={tuple(v['key']) for v in old['variables'] if v['kind']=='CHOICE'};choices={tuple(v['key']):i for i,v in enumerate(new['variables'],1) if v['kind']=='CHOICE'};owners={tuple(v['key']):i for i,v in enumerate(new['variables'],1) if v['kind']=='OWNER'};added=set(choices)-oldchoices;assert len(added)==1;added_key=next(iter(added));net=added_key[0];assert net==2 and added_key in after;z=choices[added_key];previous=[choices[key] for key in sorted(oldchoices) if key[0]==net];clauses={tuple(c):i for i,c in enumerate(new['clauses'])};origin={tuple(old['variables'][row['variable']-1]['key']):row for row in inventory['negative_options']};certificates=[]
  for key in freed:
   victim=choices[key];witnesses=sorted(w['node'] for w in origin[key]['witnesses'] if w['blocker_NET']==net);assert witnesses;node=witnesses[0];a=owners[node,net];b=owners[node,key[0]]
   raw=[[-z],previous+[z]]
   raw.extend([[-v,a] for v in previous]);raw.extend([[-victim,b],[-a,-b]])
   reduced=[sorted(set(clause)) for clause in raw];indices=[clauses[tuple(clause)] for clause in reduced]
   variables={abs(x) for clause in reduced for x in clause};model={v:False for v in variables};model[previous[0]]=True;model[a]=True
   verify(reduced,dict(status='SAT',model=model,rup_additions=[]))
   verify(reduced,dict(status='PARTIAL_RUP',model=None,rup_additions=[[-victim]]))
   certificates.append(dict(choice=key,variable=victim,node=node,original_clause_indices=indices,local_SAT_model=model,rup_additions=[[-victim]]))
  out=O/f'episode_{ep:02d}.json';out.write_text(json.dumps(dict(case=case,new_choice=added_key,new_choice_excluded_by_original_unit=True,certificates=certificates,scope='Each local subset is separately SAT, so the RUP exclusion is not vacuous from unrelated global UNSAT.'),indent=2)+'\n')
  for q in (op,np,ip,out):bindings[str(q)]=sha(q)
  row=dict(case=case,apparently_freed_initial_CHOICES=len(freed),locally_RUP_restored_exclusions=len(certificates),all_local_bases_SAT_verified=True,new_choice_initially_excluded=True);rows.append(row);print('GLOBAL_MASK_RESTORATION',json.dumps(row),flush=True)
 assert all(sha(q)==h for q,h in bindings.items())
 (O/'verification.json').write_text(json.dumps(dict(status='ALL_APPARENT_INITIAL_CHOICE_RELEASES_NONVACUOUSLY_RUP_REEXCLUDED',bindings=bindings,rows=rows,scope='Refutes apparent initial-unit coverage gain from these three isolated new choices. No general impossibility of coordinated alternatives, native routes or estimator quality.'),indent=2)+'\n')
if __name__=='__main__':main()
