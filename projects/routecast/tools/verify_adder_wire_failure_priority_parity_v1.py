"""Exact unchanged accepted state and nonaccumulating owner-ban accounting."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_wire_failure_priority_v1_2026-10-08';bindings={str(Path(__file__)):sha(__file__)};rows=[]
for step in range(4):
 p=D/f'step_{step}.json';q=E/f'adder_reverse_live_owner_v1_2026-10-08/step_{step}.json';v=json.loads(p.read_text());old=json.loads(q.read_text());assert v['state']==old['state'] and v['violation_ids']==old['violation_ids']
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';queries={x['connection_id']:x for x in json.loads(ep.read_text())['connections']};nonempty=0
 for event in v['events']:
  assert not event['committed'];pairs={(queries[a['connection_id']]['net_id'],node) for a in event['attempts'] for node in a['excluded_nodes']};assert len(pairs)<=1;nonempty+=bool(pairs)
 for f in (p,q,ep):bindings[str(f)]=sha(f)
 rows.append(dict(step=step,exact_accepted_state_unchanged=True,group_attempts=len(v['events']),attempts_reaching_banned_owner=nonempty))
out=dict(bindings=bindings,rows=rows,scope='Single owner-node ban per branch replaces old exclusions; all accepted states match previously native-certified61fail. Not exhaustive backtracking or infeasibility proof.')
(D/'parity_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
