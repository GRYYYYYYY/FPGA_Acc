"""Independent full XML channel-length and unchanged-budget failure-set accounting."""
import json,xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_shared_full_stage_6_v2_2026-10-08';B=E/'adder_shared_full_stage_5_v2_2026-10-08';r=json.loads((D/'receipt.json').read_text());m=json.loads((E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json').read_text());g=Path(m['inputs']['graph']['path']);length={};before=sha(g)
for node in ET.parse(g).getroot().find('rr_nodes'):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[int(node.get('id'))]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
assert sha(g)==before;rows=[]
for step,summary in enumerate(r['rows']):
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';queries={str(q['connection_id']):q for q in json.loads(ep.read_text())['connections']};v=json.loads((D/f'step_{step}.json').read_text());old=json.loads((B/f'step_{step}.json').read_text());unions=defaultdict(set)
 for cid,path in v['state'].items():unions[queries[cid]['net_id']].update(n for n,s in path)
 wire=sum(length.get(n,0) for ns in unions.values() for n in ns);assert wire==summary['final_wire']<=summary['baseline_wire'];assert set(v['violation_ids'])<=set(old['violation_ids'])
 cold=json.loads((E/f'adder_wire_guard_matched_cold_v7_2026-10-08/step_{step}/audit.json').read_text())
 assert set(v['violation_ids'])<=set(cold['violation_ids'])
 committed={net for e in v['events'] if e['committed'] for net in e['released_nets']}
 for cid,path in v['state'].items():
  if queries[cid]['net_id'] not in committed:assert path==old['state'][cid]
 for event in v['events']:
  if event['committed']:assert {a['connection_id'] for a in event['attempts']}=={int(cid) for cid,q in queries.items() if q['net_id'] in event['released_nets']} and all(a['status']=='FOUND' for a in event['attempts'])
 rows.append(dict(step=step,wire=wire,baseline=summary['baseline_wire'],remaining_violations=len(v['violation_ids'])))
bindings={str(p):sha(p) for p in (g,D/'receipt.json',D/'verification.json',Path(__file__))}
(D/'wire_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all4_wire_bounds_and_atomic_coverage_pass=True,scope='Independent complete channel geometry perNETunion wire, committed group fullbranch coverage, unchanged outside committed groups and no new modelbudget failures. No global CPD/native reload/gain proof.'),indent=2)+'\n');print(rows)
