"""Independent complete match-set and posting candidate validation."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_nogood_index_2026-10-06';parent=root/'experiments/nonzero_rc_resolved_backjump_2026-10-06';r=json.loads((out/'receipt.json').read_text());source=json.loads((parent/'receipt.json').read_text());assert r['parent_sha256']==sha(parent/'receipt.json') and r['protocol_sha256']==sha(out/'protocol.json') and r['source_sha256']==sha(root/'tools/trial_nonzero_rc_nogood_index.py');cores=[set(map(tuple,c)) for c in source['nogoods']];frequency=Counter(lit for c in cores for lit in c);assert r['cores']==len(cores)==len(r['anchors'])
for core,anchor in zip(cores,r['anchors']):assert (tuple(anchor)==min(core,key=lambda x:(frequency[x],x))) if core else anchor is None
stack=[(source['proof'],{})];snapshots=[]
while stack and len(snapshots)<256:
 p,decisions=stack.pop()
 if 'limit' in p:continue
 snapshots.append(decisions)
 for c in reversed(p.get('children',[])):stack.append((c['proof'],{**decisions,p['branch']:c['candidate']}))
assert len(r['records'])==len(snapshots)==256;indexed=0
for record,decisions in zip(r['records'],snapshots):
 assert record['decisions']==[list(v) for v in sorted(decisions.items())];active=set(decisions.items())
 candidates=[i for i,anchor in enumerate(r['anchors']) if anchor is None or tuple(anchor) in active];matches=[i for i,core in enumerate(cores) if core<=active]
 assert candidates==record['candidate_indices'] and matches==record['matches'] and set(matches)<=set(candidates);indexed+=len(candidates)
assert r['indexed_core_tests']==indexed and r['linear_core_tests']==len(cores)*256
(out/'verification.json').write_text(json.dumps({'states_checked':256,'cores':len(cores),'all_applicable_conflicts_preserved':True,'linear_core_tests':r['linear_core_tests'],'indexed_core_tests':indexed,'receipt_sha256':sha(out/'receipt.json'),'scope':'Exact match-set equality on frozen final learned library and authenticated historical decision snapshots; no online trajectory, timing, complete prediction or native legality claim.'},indent=2)+'\n');print('verified256 snapshots; all matches preserved')
