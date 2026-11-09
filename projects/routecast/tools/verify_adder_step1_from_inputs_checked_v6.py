"""Independent physical/Fraction and partial-state replay of joint NET rerouting."""
import json,hashlib
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_step1_from_inputs_checked_v6_2026-10-09';D=E/'adder_step1_from_inputs_checked_verification_v6_2026-10-09';D.mkdir(exist_ok=False);rp=B/'verification.json';report=json.loads(rp.read_text());bindings={**report['bindings'],str(rp):sha(rp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());dp=B/'result.json';data=json.loads(dp.read_text());ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json';meta=json.loads(ep.read_text());q={x['connection_id']:x for x in meta['connections']};bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_1_budgets.json';budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);bank={int(c):opts for c,opts in data['bank'].items()};assert set(bank)==set(q)
for cid,options in bank.items():
 assert options
 for option in options:
  path=option['path'];assert path[0]==[q[cid]['source'],None] and path[-1][0]==q[cid]['sink'] and len({n for n,s in path})==len(path);r,c=inv.classes[inv.node_classes[q[cid]['source']]];delay=r*c/2
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1;r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  assert delay==F(*option['exact_delay_s']) and delay<=budgets[cid]
from verify_certified_cnf_dependency_cdcl_v1 import verify
from independent_route_cnf_structure_v1 import verify_encoding
rounds=0;events=0
for row in data['rounds']:
 artifact=B/f"round_{row['iteration']}.json"
 if not artifact.exists():
  assert row.get('full_status')=='SAT' or row['capacity_status']=='UNKNOWN_SEARCH_LIMIT';continue
 record=json.loads(artifact.read_text());cnf=record['encoding'];counts=defaultdict(int)
 for role in cnf['variables']:
  if role['kind']=='PATH':cid,index=role['key'];counts[cid]=max(counts[cid],index+1)
 options={c:bank[c][:count] for c,count in counts.items()};assert set(options)==set(q);verify_encoding(cnf,options,q,inv);indices=record['retained_indices'];clauses=[cnf['clauses'][i] for i in indices];assert indices==list(range(len(cnf['clauses']))) or indices==[i for i,c in enumerate(cnf['clauses']) if all(cnf['variables'][abs(x)-1]['kind']!='NET_PARENT' for x in c)];verify(clauses,record['proof_result']);core=record['core_clause_indices'];assert all(0<=i<len(clauses) for i in core)
 # Full proof is checked; support subset has a separate complete proof requirement.
 for event in record['events']:
  if event['status']=='FOUND':
   cid=event['connection_id'];path=event['path'];assert any(o['path']==path for o in bank[cid]);assert not set(event['blocked_nodes'])&{n for n,s in path};assert [inv.physical.arcs[u,v,s] for (u,_),(v,s) in zip(path,path[1:])]==event['physical_edge_ids']
  else:assert event['status'] in ('NO_STRICT_IMPROVEMENT','LABEL_LIMIT')
  events+=1
 bindings[str(artifact)]=sha(artifact);rounds+=1
if data['selection'] is not None:
 tp=B/'terminal_sat.json';terminal=json.loads(tp.read_text());cnf=terminal['encoding'];verify_encoding(cnf,bank,q,inv);verify(cnf['clauses'],terminal['result']);assert terminal['result']['status']=='SAT';model={int(c):v for c,v in terminal['result']['model'].items()};assert set(model)==set(range(1,len(cnf['variables'])+1));selection={int(c):i for c,i in data['selection'].items()};assert set(selection)==set(q) and len(selection)==516;owners=defaultdict(set);parents=defaultdict(dict)
 for cid,index in selection.items():
  chosen=[i for i in range(len(bank[cid])) if model[cnf['path_vars'][f'{cid}:{i}']]];assert chosen==[index];path=bank[cid][index]['path'];assert path==data['paths'][str(cid)];net=q[cid]['net_id']
  for n,s in path:owners[n].add(net)
  for (u,_),(n,s) in zip(path,path[1:]):assert n not in parents[net] or parents[net][n]==(u,s);parents[net][n]=(u,s)
 assert all(len(nets)<=int(inv.physical.nodes[n][1]) for n,nets in owners.items());bindings[str(tp)]=sha(tp);sp=D/'selection.json';sp.write_text(json.dumps(dict(selection=data['selection'],paths=data['paths']),indent=2)+'\n');bindings[str(sp)]=sha(sp)
else:assert data['paths'] is None
phase_report=json.loads(rp.read_text());assert all(type(x) in (int,float) and x>=0 for x in phase_report['phase_seconds'].values());assert sum(phase_report['phase_seconds'].values())<=phase_report['component_seconds'];assert phase_report['phase_calls']['encoding']==len(data['rounds']);assert phase_report['phase_calls']['proof_support']==rounds
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,candidates=sum(map(len,bank.values())),rounds=rounds,events=events,status='FULL516_MODEL_PHYSICAL_BUDGET_CAPACITY_PARENT_PASS' if data['selection'] is not None else 'BOUNDED_CANDIDATES_AND_ROUND_FORMULAS_PROOFS_VERIFIED',scope='All candidate original physical/Fraction budget; each round full original encoding independently rebuilt and RUP verified; successful detour blocked-node and edge paths checked. Support minimality, exact generating query replay and full candidate-free provenance not inferred from final bank alone. SAT if present includes exact full model and independent all516physical/budget/capacity/parent; native/canonical and cost pending.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
