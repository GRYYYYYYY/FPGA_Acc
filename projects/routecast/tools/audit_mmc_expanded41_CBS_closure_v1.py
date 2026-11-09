"""Check complete conflict-branch coverage using independently checked certificates.

A query budget failure closes its mask subdomain. Every resource-use conflict
is a necessary disjunction, verified upstream; all children must be closed.
The monotone forbidden-resource sets form a finite acyclic proof graph.
"""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_expanded41_conflict_first_CBS_v1_2026-10-21';P=D/'verification.json';A=D/'independent_verification_v1.json';v=json.loads(P.read_text());a=json.loads(A.read_text());assert all(sha(p)==h for p,h in a['bindings'].items());assert all(sha(p)==h for k in ['bindings','files'] for p,h in v[k].items());oldp=R/'experiments/mmc_cover_plus151_residual_v1_2026-10-21/verification.json';old=json.loads(oldp.read_text());selectionp=R/'experiments/mmc_expanded40_joint_CBS_v1_2026-10-21/next41_protocol_v1.json';selection=json.loads(selectionp.read_text());bindings={str(p):sha(p) for p in [P,A,oldp,selectionp,Path(__file__)]};rows=[]
def key(masks):return tuple((n,tuple(sorted(rs))) for n,rs in sorted(masks.items()) if rs)
for case_row in v['rows']:
 case=case_row['case'];assert case_row['status']=='EXHAUSTED_FIXED_DOMAIN';root={i['net_id']:i['result'] for i in old['rows'] if i['case']==case};paths=sorted((D/case).glob('query_*/result.json'));queries=[json.loads(p.read_text()) for p in paths];newnets=selection['new_NETs'][case];nr=len(newnets)
 for net,p,q in zip(newnets,paths,queries):assert q['net_id']==net and q['extra_forbidden']==[] and q['all_connections_within_budget'];root[net]=str(p)
 states={0:({},root)};registry={key({}):0};assessed=[];children=0;budget_prunes=0
 for event in case_row['events']:
  if 'parent' not in event:
   sid=event['state'];assert sid in states;assessment_path=D/case/('assessment_%03d.json'%(len(assessed)+1));state=json.loads(assessment_path.read_text());assert state['trees']=={str(n):p for n,p in states[sid][1].items()};assert state['conflict']==event['conflict'];assert not (state['result'] and state['result']['satisfiable']);assessed.append(sid);continue
  sid,parent=event['state'],event['parent'];net,node=event['forbidden'];assert parent in states and sid not in states;pm,pt=states[parent];cm={n:set(rs) for n,rs in pm.items()};assert node not in cm.get(net,set());cm.setdefault(net,set()).add(node);ck=key(cm);assert ck not in registry;registry[ck]=sid
  q=queries[nr+children];path=paths[nr+children];children+=1;assert q['net_id']==net and q['extra_forbidden']==sorted(cm[net]);assert event['pruned']==(not q['all_connections_within_budget'])
  if event['pruned']:budget_prunes+=1;continue
  ct=dict(pt);ct[net]=str(path);states[sid]=(cm,ct)
 assert children+nr==len(queries) and len(assessed)==len(set(assessed)) and set(assessed)==set(states)
 for index,sid in enumerate(assessed,1):
  state=json.loads((D/case/('assessment_%03d.json'%index)).read_text());masks,trees=states[sid]
  for net,node in state['conflict']:
   child={n:set(rs) for n,rs in masks.items()};assert node not in child.get(net,set());child.setdefault(net,set()).add(node);assert key(child) in registry
 rows.append({'case':case,'closed_assessed_states':len(assessed),'certified_budget_pruned_children':budget_prunes,'all_conflict_disjunction_children_covered':True,'fixed_domain_UNSAT_certified':True})
assert all(sha(p)==h for p,h in bindings.items());out={'status':'BOTH_FIXED_EXPANDED_ROUTABLE_DOMAINS_CLOSED_BY_CHECKED_MONOTONE_RESOURCE_BRANCH_PROOFS','rows':rows,'bindings':bindings,'scope':'Only case02 extended set original37-case02 plus40/96 and case03 original37-case03 plus2450, fixed old37 keeper masks, remaining frozen A/B bank and unchanged model budgets. General RR, other masks/covers/expanded NETs, prediction or gain are not covered.'};(D/'independent_branch_closure_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
