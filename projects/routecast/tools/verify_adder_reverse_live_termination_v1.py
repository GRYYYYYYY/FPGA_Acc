"""Replayed algorithm parity and group stopping-reason accounting."""
import json
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_reverse_live_termination_v1_2026-10-08';B=E/'adder_reverse_live_owner_v1_2026-10-08';receipt=json.loads((D/'receipt.json').read_text());assert all(sha(p)==h for p,h in receipt['bindings'].items());rows=[];bindings={str(D/'receipt.json'):sha(D/'receipt.json'),str(Path(__file__)):sha(__file__)}
for step in range(4):
 p=D/f'step_{step}.json';q=B/f'step_{step}.json';v=json.loads(p.read_text());old=json.loads(q.read_text());groups=defaultdict(list);counts=Counter();last=Counter();pending=0
 for e in v['events']:groups[e['target_net']].append(e)
 for events in groups.values():
  ends=[e for e in events if 'termination' in e];assert len(ends)==1 and ends[0] is events[-1];term=ends[0]['termination'];reason=term['reason'];counts[reason]+=1;last[str(term['last_witness_status'])]+=1
  assert [e['retry'] for e in events]==list(range(len(events))) and len(events)<=32
  if reason=='COMMITTED':assert events[-1]['committed']
  elif reason=='GROUP_ATTEMPT_LIMIT':assert len(events)==32 and not events[-1]['committed']
  elif reason=='FRONTIER_EMPTY':assert term['pending_candidates']==0 and not events[-1]['committed']
  else:assert reason=='REPEATED_SIGNATURE'
  pending+=term['pending_candidates']
 for e in v['events']:e.pop('termination',None)
 assert v==old
 for f in (p,q):bindings[str(f)]=sha(f)
 rows.append(dict(step=step,full_algorithm_trace_parity=True,termination_counts=dict(counts),last_witness_status_counts=dict(last),pending_queue_items_at_stop=pending))
out=dict(bindings=bindings,rows=rows,scope='Stopping reasons for same frozen66->61 algorithm replay. Queue count excludes popped next candidate at attempt limit; conditional failures not global infeasibility.')
(D/'termination_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
