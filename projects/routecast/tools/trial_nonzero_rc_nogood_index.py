"""Exact frozen-library lookup replay, not a new search or timing claim."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_resolved_backjump_2026-10-06';out=root/'experiments/nonzero_rc_nogood_index_2026-10-06';out.mkdir();r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json');cores=[tuple(map(tuple,c)) for c in r['nogoods']];frequency=Counter(lit for c in cores for lit in c);postings=defaultdict(list);empty=[];anchors=[]
(out/'protocol.json').write_text(json.dumps({'parent_sha256':sha(parent/'receipt.json'),'states':256,'policy':'Freeze entire verified final conflict library; anchor each nonempty core on least frequent literal (literal tie); union postings for active decisions and exact-check candidates; compare ALL matches with linear scan on first256 depth-first historical proof states','scope':'Replay can use conflicts learned later than historical state because it is a separate frozen-library experiment; no same-trajectory online/timing claim'},indent=2)+'\n')
for i,c in enumerate(cores):
 if not c:empty.append(i);anchors.append(None)
 else:anchor=min(c,key=lambda x:(frequency[x],x));anchors.append(anchor);postings[anchor].append(i)
snapshots=[]
def collect(p,decisions):
 if len(snapshots)>=256:return
 if 'limit' in p:return
 snapshots.append(dict(decisions))
 for child in p.get('children',[]):collect(child['proof'],{**decisions,p['branch']:child['candidate']})
collect(r['proof'],{});records=[];linear_tests=0;indexed_tests=0
for decisions in snapshots:
 expected=[i for i,c in enumerate(cores) if all(decisions.get(k)==a for k,a in c)];linear_tests+=len(cores)
 candidates=set(empty)
 for literal in decisions.items():candidates.update(postings.get(literal,()))
 actual=[i for i in sorted(candidates) if all(decisions.get(k)==a for k,a in cores[i])];indexed_tests+=len(candidates);assert expected==actual
 records.append({'decisions':sorted(decisions.items()),'candidate_indices':sorted(candidates),'matches':actual})
result={'anchors':anchors,'records':records,'cores':len(cores),'linear_core_tests':linear_tests,'indexed_core_tests':indexed_tests,'parent_sha256':sha(parent/'receipt.json'),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('states',len(records),'linear checks',linear_tests,'indexed checks',indexed_tests)
