"""Same full21619 point identities, compare proof outcomes without merging certificates."""
import json,re
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];paths=[R/'experiments/supported_archived_json_equivalence_cohort_v2_2026-10-10/stereovision0',R/'experiments/diffeq2_stereo0_full_equivalence_alternative_v1_2026-10-10/stereovision0'];bindings={str(Path(__file__).resolve()):sha(Path(__file__))};attempts=[]
for d in paths:
 p=d/'receipt.json';v=json.loads(p.read_text());assert v['exit_code']==1 and all(sha(k)==h for k,h in v['bindings'].items());lp=d/'equivalence.log';bindings.update({str(x):sha(x) for x in [p,lp]});a={}
 for line in lp.read_text().splitlines():
  m=re.match(r'^\s*Trying to prove \$equiv for (.+): (success!|failed\.)$',line)
  if m:assert m[1] not in a;a[m[1]]=m[2]=='success!'
 assert len(a)==21619;attempts.append(a)
assert attempts[0].keys()==attempts[1].keys();rows=[dict(point=p,original_proved=attempts[0][p],alternative_proved=attempts[1][p]) for p in sorted(attempts[0])];counts=Counter(('proved' if x['original_proved'] else 'unproved')+'->'+('proved' if x['alternative_proved'] else 'unproved') for x in rows);jp=paths[1]/'pre_induction_equiv.json';m=json.loads(jp.read_text())['modules']['equiv'];outputnames={p for p,d in m['ports'].items() if d['direction']=='output'};topchanges=[x for x in rows if x['original_proved']!=x['alternative_proved'] and re.sub(r' \[\d+\]$','',x['point']).lstrip('\\') in outputnames];D=R/'experiments/stereovision0_complete_proof_comparison_v1_2026-10-10';assert not D.exists();D.mkdir();bindings[str(jp)]=sha(jp);(D/'comparison.json').write_text(json.dumps(dict(bindings=bindings,all21619_point_results=rows,transition_counts=dict(counts),changed_top_output_points=topchanges,scope='All logged simple obligations same identities compared, both final checks fail. Set comparison only; no union proof certificate, chosen method/point deletion, initialization/full temporal/native/family admission.'),indent=2)+'\n');print(dict(counts));print(topchanges)
