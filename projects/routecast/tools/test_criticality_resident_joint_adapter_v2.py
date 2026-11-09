"""CSR identities, duplicate pins, exact independent shared-node scoring."""
import random,copy,json,itertools
from pathlib import Path
from fractions import Fraction
from criticality_resident_joint_adapter_v2 import fallback
from pre_route_endpoints import sha
fields=dict(row_offsets=[0,3,5,5,5],dest_ranks=[1,2,3,2,3],edge_ids=[10,11,12,13,14],capacities=[1]*4)
slots={e:i for i,e in enumerate(fields['edge_ids'])};inc=[1,4,4,1,1]
class RC:
 def initial(self,u):return 0
 def increment(self,slot):return inc[slot]
 def path(self,source,sink,path):
  u=source;raw=0
  for eid in path:
   slot=slots[eid];assert fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1];u=fields['dest_ranks'][slot];raw+=inc[slot]
  assert u==sink;return raw
rc=RC();queries=[dict(connection_id=0,source=0,sink=2),dict(connection_id=1,source=0,sink=3),dict(connection_id=2,source=0,sink=2)]
old=[dict(q,budget_integer=8,answer=dict(status='FOUND',physical_edge_ids=[11 if q['sink']==2 else 12],delay=4)) for q in queries]
parents={1:(0,0),2:(1,3),3:(1,4)};rng=random.Random(7811);accepts=0;legacy_disagreements=0
for trial in range(300):
 prices={u:rng.randrange(20) for u in range(4)};base=[rng.randrange(10) for _ in range(4)];weight=rng.randrange(4)
 criticalities={q['connection_id']:dict(source_rr=0,target_rr=q['sink'],criticality_numerator=rng.randrange(9),criticality_denominator=8) for q in queries}
 frozen=copy.deepcopy((fields,queries,old,parents,prices,base,criticalities))
 result=fallback(fields,rc,slots,queries,old,parents,{2,3},prices,weight,base,criticalities)
 assert (fields,queries,old,parents,prices,base,criticalities)==frozen
 def independent(paths):
  users={};total=Fraction(0)
  for q in queries:
   c=Fraction(criticalities[q['connection_id']]['criticality_numerator'],8);u=0;raw=0
   for e in paths[q['sink']]:
    slot=slots[e];u=fields['dest_ranks'][slot];raw+=inc[slot];users.setdefault(u,[]).append(c)
   total+=c*raw
  return total+sum(((1-max(cs))*(base[u]+weight*prices[u]) for u,cs in users.items()),Fraction(0))
 valid=[]
 for a,b in itertools.product([[11],[10,13]],[[12],[10,14]]):
  valid.append(independent({2:a,3:b}))
 assert result['chosen_score']==min(valid) and result['old_score']==independent({2:[11],3:[12]})
 assert result['chosen_score']<=result['old_score']
 accepts+=result['status']=='ACCEPT_STRICT_IMPROVEMENT'
 legacy_disagreements+=result['status']!=result['legacy_status']
 for r in result['records']:assert r['answer']['delay']==rc.path(0,r['sink'],r['answer']['physical_edge_ids'])<=r['budget_integer']
 limited=fallback(fields,rc,slots,queries,old,parents,{2,3},prices,weight,base,criticalities,max_states=1)
 assert limited['chosen_score']<=limited['old_score'] and limited['search_status']=='UNKNOWN_STATE_LIMIT'
# Wrong frozen endpoint must be rejected before selection; caller unchanged.
bad=copy.deepcopy(criticalities);bad[0]['target_rr']=1
try:fallback(fields,rc,slots,queries,old,parents,{2,3},prices,weight,base,bad)
except ValueError:pass
else:raise AssertionError('identity mismatch admitted')
out=Path('experiments/criticality_resident_joint_adapter_contract_v2_2026-10-10');out.mkdir()
files=[Path(__file__).resolve()]+[Path('tools')/name for name in ['criticality_resident_joint_adapter_v2.py','criticality_whole_net_choice_reference_v1.py','criticality_whole_net_choice_undo_v1.py','resident_actual_old_fallback_undo_adapter_v2.py','budget_actual_old_acceptance_undo_v2.py','budget_joint_candidates_undo_v3.py','budget_NET_gate_reference_v1.py']]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p.resolve()):sha(p) for p in files},cases=300,accepted=accepts,legacy_status_disagreements=legacy_disagreements,independent_score_and_candidate_optimum_pass=True,no_caller_mutation_and_endpoint_rejection_pass=True,scope='One shared-branch CSR topology, randomized costs/per-pin criticalities/duplicate sink. Full MMC and arbitrary graph adapter validation remain open.'),indent=2)+'\n')
print('CRITICALITY CSR JOINT ADAPTER PASS',300,accepts,'legacy status disagreements',legacy_disagreements)
