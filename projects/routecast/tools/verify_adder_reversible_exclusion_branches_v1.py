"""Check baseline-derived independent sibling exclusions and unchanged states."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_reversible_exclusion_v1_2026-10-08';r=json.loads((D/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items())
m=json.loads((E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json').read_text());g=Path(m['inputs']['graph']['path']);digest=sha(g);root=ET.parse(g).getroot();edges={i:tuple(int(e.get(k)) for k in ('src_node','sink_node','switch_id')) for i,e in enumerate(root.find('rr_edges'))};assert sha(g)==digest
rows=[]
for step in range(4):
 v=json.loads((D/f'step_{step}.json').read_text());oldpath=E/f'adder_failure_priority_retry_v1_2026-10-08/step_{step}.json';old=json.loads(oldpath.read_text());assert v['state']==old['state'];groups={};siblings=0
 for e in v['events']:groups.setdefault(e['target_net'],[]).append(e)
 for events in groups.values():
  assert [e['retry'] for e in events]==list(range(len(events))) and len(events)<=16
  baseline={(a['connection_id'],edges[i][1]) for a in events[0]['attempts'] if a['status']=='FOUND' for i in a['physical_edge_ids']};signatures=set()
  for e in events:
   assert not e['committed'];excluded={(a['connection_id'],n) for a in e['attempts'] for n in a['excluded_nodes']};assert len(excluded)<=1
   if excluded:assert excluded<=baseline;siblings+=1
   # A branch may fail before reaching its scheduled excluded CID.
   if excluded:assert tuple(sorted(excluded)) not in signatures;signatures.add(tuple(sorted(excluded)))
   for a in e['attempts']:
    if a['status']=='FOUND':assert not {edges[i][1] for i in a['physical_edge_ids']}.intersection(a['excluded_nodes'])
 rows.append(dict(step=step,independent_siblings_reaching_excluded_connection=siblings,group_attempts=len(v['events']),state_exactly_unchanged=True))
out=dict(bindings={str(p):sha(p) for p in (D/'receipt.json',Path(__file__),g)},rows=rows,scope='Depth-one baseline node-exclusion siblings with reset, not exhaustive path/NET backtracking. No new accepted candidate.')
(D/'branch_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
