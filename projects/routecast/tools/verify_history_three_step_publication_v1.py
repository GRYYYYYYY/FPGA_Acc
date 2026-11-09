"""Independent original-XML physical/Fraction audit of three committed epochs."""
import json
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as F
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'history_three_step_publication_v1_2026-10-09';D=E/'history_three_step_publication_verification_v1_2026-10-09'
rp=B/'verification.json';receipt=json.loads(rp.read_text());bindings={**receipt['bindings'],str(rp):sha(rp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());D.mkdir(exist_ok=False)
rows=[];inv=None
assert [r['step'] for r in receipt['rows']]==[1,2,3]
for step,namespace in [(1,'fresh_history_workflow_v1_stage_2_2026-10-09'),(2,'history_step2_v1_stage_2_2026-10-09'),(3,'history_step3_v1_stage_2_2026-10-09')]:
 p=B/f'step_{step}_committed.json';doc=json.loads(p.read_text());assert doc['epoch']==step
 authority=E/namespace/'result.json';assert doc['paths']==json.loads(authority.read_text())['paths']
 ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';meta=json.loads(ep.read_text());q={x['connection_id']:x for x in meta['connections']}
 budgetp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json';budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(budgetp.read_text())}
 if inv is None:inv=read(meta['inputs']['graph']['path'],meta['graph_sha256'])
 assert meta['graph_sha256']==sha(meta['inputs']['graph']['path'])
 paths={int(c):path for c,path in doc['paths'].items()};assert set(paths)==set(q)==set(budgets) and len(paths)==516
 owners=defaultdict(set);parents=defaultdict(dict)
 for cid,path in paths.items():
  query=q[cid];net=query['net_id'];assert path[0]==[query['source'],None] and path[-1][0]==query['sink'];assert len({n for n,s in path})==len(path)
  r,c=inv.classes[inv.node_classes[query['source']]];delay=r*c/2
  for n,s in path:owners[n].add(net)
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1
   nr,nc=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+nr/2)*nc+td
   assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
  assert delay<=budgets[cid]
 assert all(len(nets)<=int(inv.physical.nodes[n][1]) for n,nets in owners.items())
 row=receipt['rows'][step-1];assert row['prior_epoch']==step-1 and row['committed_epoch']==step
 assert all(row[k] for k in ['all_failure_state_epoch_preserved','validator_rejection_atomic','one_concurrent_commit_one_stale','stale_commit_rejected','complete_target_matches'])
 for f in (p,authority,ep,budgetp):bindings[str(f)]=sha(f)
 rows.append(dict(step=step,epoch=doc['epoch'],connections=len(paths),physical_exact_budget_capacity_parent_pass=True))
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Independent original physical arcs, Fraction model budgets, NET capacity/shared parent for three published epochs and exact equality to native-certified selections. Fault execution evidence inherited from authenticated receipt; not native rollback or disk durability.'),indent=2)+'\n');print(rows)
