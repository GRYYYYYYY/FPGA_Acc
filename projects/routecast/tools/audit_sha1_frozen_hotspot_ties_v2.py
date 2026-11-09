"""Frozen predicted ordering, all admissible truth cutoff tie choices; no k tuning."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/sha1_frozen_hotspots_v2_2026-10-10/sha1'
p=D/'comparison.json';r=json.loads(p.read_text());assert all(sha(k)==h for k,h in r['bindings'].items())
vp=D/'comparison_vectors.json';v=json.loads(vp.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(p):sha(p),str(vp):sha(vp)}
rows=[]
for domain,source in [('concrete','channels'),('spatial','bins')]:
 values=v[source];ids=[x['node'] if domain=='concrete' else tuple(x['key']) for x in values]
 truth={i:x['native']/x['capacity'] for i,x in zip(ids,values)}
 for method,metrics in r['metrics'].items():
  m=metrics[domain]
  if m is None:continue
  predicted={i:(x['geometry'] if method=='geometry' else x['predictions'][method]/x['capacity']) for i,x in zip(ids,values)}
  k=m['k'];boundary=m['truth_k_boundary'];strict={i for i in ids if truth[i]>boundary};ties={i for i in ids if truth[i]==boundary}
  selected=set(sorted(ids,key=lambda i:(-predicted[i],i))[:k]);need=k-len(strict);assert 0<need<=len(ties)
  fixed=len(selected&strict);possible=len(selected&ties)
  lo=fixed+max(0,need-(len(ties)-possible));hi=fixed+min(need,possible)
  actual=m['precision_at_k'];assert lo/k<=actual<=hi/k
  rows.append(dict(domain=domain,method=method,k=k,truth_cutoff=boundary,truth_strict_count=len(strict),truth_cutoff_ties=len(ties),ties_to_select=need,reported_id_tiebroken_precision=actual,truth_tie_precision_lower=lo/k,truth_tie_precision_upper=hi/k))
assert all(sha(k)==h for k,h in bindings.items())
(D/'truth_tie_sensitivity.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='All truth top-k sets allowed by cutoff ties for fixed predicted ID ordering; not joint uncertainty over predicted ties. Descriptive development diagnostics, no changed k, heldout or native failure prediction proof.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
