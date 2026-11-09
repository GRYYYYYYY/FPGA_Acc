"""Verify bounded expansion transitions and authenticated group accounting."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/adder_live_owner_expansion_v1_2026-10-08';r=json.loads((D/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items());rows=[]
for step in range(4):
 v=json.loads((D/f'step_{step}.json').read_text());groups={}
 for e in v['events']:groups.setdefault(e['target_net'],[]).append(e)
 for events in groups.values():
  assert [e['retry'] for e in events]==list(range(len(events))) and len(events)<=32
  assert not any(e['committed'] for e in events[:-1])
  for prev,nxt in zip(events,events[1:]):
   if prev.get('expanded_external_owners'):
    assert not set(prev['expanded_external_owners']).intersection(prev['released_nets'])
    assert set(prev['released_nets'])|set(prev['expanded_external_owners'])==set(nxt['released_nets'])
 rows.append(dict(step=step,expansion_events=sum(bool(e.get('expanded_external_owners')) for e in v['events']),max_released_nets=max(len(e['released_nets']) for e in v['events']),successful_group_sizes=[len(e['released_nets']) for e in v['events'] if e['committed']]))
out=dict(bindings={str(p):sha(p) for p in (D/'receipt.json',Path(__file__))},rows=rows,scope='Expansion event transitions and pergroup bounded attempt accounting; final route correctness separately verified.')
(D/'expansion_accounting.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
