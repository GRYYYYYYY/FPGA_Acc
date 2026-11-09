import sys,json,random,copy,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from terminal_assignment_feasibility_v1 import match,terminal_index,probe
rng=random.Random(1730)
for trial in range(500):
 n=rng.randrange(1,8);m=rng.randrange(0,7);caps={p:rng.randrange(3) for p in range(m)}
 rows={r:[p for p in caps if rng.randrange(2)] for r in range(n)};answer=match(rows,caps);deficiency=0
 for bits in range(1<<n):
  subset=[r for r in rows if bits&(1<<r)];neighbors={p for r in subset for p in rows[r]}
  deficiency=max(deficiency,len(subset)-sum(caps[p] for p in neighbors))
 assert answer['matched']==n-deficiency and answer['hall_deficit']==deficiency
 assert answer['feasible']==(deficiency==0)
 if deficiency:
  assert set(answer['hall_resources'])=={p for r in answer['hall_rows'] for p in rows[r]}
f=dict(row_offsets=[0,2,4,5,6,7,7],dest_ranks=[1,2,3,4,3,5,5],edge_ids=list(range(7)),capacities=[2,1,1,1,1,2])
kinds=['SOURCE','CHANX','CHANY','IPIN','IPIN','SINK']
class RC:
 def __init__(self,costs):self.costs=costs
 def increment(self,s):return self.costs[s]
 def path(self,source,sink,path):
  u=source;seen={u};cost=0
  for edge in path:
   slots=[s for s in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['edge_ids'][s]==edge];assert len(slots)==1
   s=slots[0];u=f['dest_ranks'][s];assert u not in seen;seen.add(u);cost+=self.costs[s]
  assert u==sink;return cost
records=[dict(connection_id=0,net_id=0,source=0,sink=5,answer=dict(status='FOUND',physical_edge_ids=[0,2,5],delay=3),budget_integer=3),
         dict(connection_id=1,net_id=1,source=0,sink=5,answer=dict(status='FOUND',physical_edge_ids=[1,4,5],delay=3),budget_integer=3)]
ledger={0:2,1:1,2:1,3:2,5:2};info,pools=terminal_index(f,kinds);saved=copy.deepcopy((records,ledger,f,info,pools))
ok=probe(5,records,ledger,f,kinds,RC([1]*7),{i:i for i in range(7)},info,pools)
assert ok['status']=='FEASIBLE_PREFIX_BUDGET_PROPOSAL' and ok['matching']['matching']=={0:4,1:3}
assert (records,ledger,f,info,pools)==saved
old_channels=Counter();new_channels=Counter()
for r in records:
 old_channels.update({f['dest_ranks'][e] for e in r['answer']['physical_edge_ids'] if kinds[f['dest_ranks'][e]].startswith('CHAN')})
for r in ok['assignments']:
 new_channels.update({f['dest_ranks'][e] for e in r['physical_edge_ids'] if kinds[f['dest_ranks'][e]].startswith('CHAN')})
assert old_channels==new_channels
blocked=probe(5,records,ledger,f,kinds,RC([1,1,1,4,1,1,1]),{i:i for i in range(7)},info,pools)
assert blocked['status']=='HALL_DEFICIENT_PREFIX_BUDGET_GRAPH' and blocked['matching']['hall_deficit']==1
repeated=copy.deepcopy(records);repeated[1]['net_id']=0
assert probe(5,repeated,ledger,f,kinds,RC([1]*7),{i:i for i in range(7)},info,pools)['status']=='UNSUPPORTED_REPEATED_NET_IN_CLASS'
disabled=copy.deepcopy(f);disabled['capacities'][4]=0
assert probe(5,records,ledger,disabled,kinds,RC([1]*7),{i:i for i in range(7)},info,pools)['status']=='UNSUPPORTED_NONUNIT_OR_MISSING_IPIN_POOL'
D=R/'experiments/terminal_assignment_feasibility_core_v1_2026-10-18';D.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (D/'verification.json').open('x') as out:json.dump(dict(status='pass',bindings={str(p):sha(p) for p in [Path(__file__).resolve(),R/'tools/terminal_assignment_feasibility_v1.py']},random_graphs=500,matching_and_Hall_deficiency_equal_exhaustive_subset_oracle=True,physical_toy_prefix_witness_and_budget_exclusion_pass=True,channel_path_conservation_and_input_nonmutation_pass=True,repeated_NET_and_nonunit_pool_rejected=True,scope='Tiny directed graph and exact matching core only. No native dataset admission, objective-approved model update, full routing or performance evidence.'),out,indent=2)
print('TERMINAL ASSIGNMENT CORE PASS 500 exhaustive-Hall comparisons and physical/budget fixtures')
