"""Authenticated full event and connection-occurrence coverage, not success-only rates."""
import json,sys
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_joint_frozen_candidates_full_sink_v3_2026-10-09'
bindings=closure([Path(__file__)])
def load(p):
 bindings[str(p)]=sha(p);return json.loads(p.read_text())
proof=load(D/'verification.json');assert proof['all_original_XML_Fraction_selected_trees_budget_parent_and_membership_checks_pass']
for p,h in proof['bindings'].items():assert sha(p)==h;bindings[p]=h
attempts=load(R/'experiments/mmc_triangular_retained_attempt_replay_v1_2026-10-09/attempts.json')
queries={(row['round'],row['net_id']):len(row['attempts']) for row in attempts}
rows=load(D/'selections.json');assert len(rows)==2192 and len(queries)==2192
buckets=defaultdict(lambda:dict(events=0,connection_occurrences=0,selected_connection_occurrences=0,lower_initial_objective_events=0,search_states=0))
for row in rows:
 n=queries[row['round'],row['net_id']]
 size='1' if n==1 else ('2-10' if n<=10 else ('11-100' if n<=100 else ('101-500' if n<=500 else '>500')))
 for key in ('ALL',f"round{row['round']}",f"status:{row['status']}",f"size:{size}"):
  b=buckets[key];b['events']+=1;b['connection_occurrences']+=n;b['search_states']+=row['states']
  if row['paths'] is not None:
   b['selected_connection_occurrences']+=n
   b['lower_initial_objective_events']+=row['union_cost']<row['old_union_cost']
assert buckets['ALL']['events']==2192 and buckets['ALL']['connection_occurrences']==80868
assert sum(b['connection_occurrences'] for k,b in buckets.items() if k.startswith('status:'))==80868
assert all(sha(p)==h for p,h in bindings.items())
r=dict(bindings=bindings,buckets=dict(buckets),scope='Post-audit descriptive full event/connection occurrence coverage. Repeated NETs across rounds not unique samples. Initial witness objective difference is not actual old-tree gain, congestion reduction, native QoR or complete speedup.')
(D/'coverage.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['buckets'],indent=2))
