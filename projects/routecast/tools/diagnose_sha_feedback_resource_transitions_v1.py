"""Complete discrete-resource feedback error accounting; descriptive exposed-development diagnosis."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_feedback_resource_transitions_v1_2026-10-10';assert not D.exists();D.mkdir()
bindings={str(Path(__file__).resolve()):sha(Path(__file__))};rows=[]
for case,root in [('original','sha1_frozen_hotspots_v2_2026-10-10'),('second_swap','sha_second_swap_hotspots_v1_2026-10-10')]:
 B=R/'experiments'/root/'sha1';vp=B/'comparison_vectors.json';mp=B/'metric_verification.json';proof=json.loads(mp.read_text());assert proof['histogram_ranks_topk_mae_and_full_vector_scope_pass'] and all(sha(p)==h for p,h in proof['bindings'].items());bindings.update({str(p):sha(p) for p in [vp,mp]});v=json.loads(vp.read_text());cs=v['channels'];assert len(cs)==28188 and len({x['node'] for x in cs})==len(cs) and all(x['capacity']==1 and x['native'] in [0,1] for x in cs)
 for method in ['round0_shared','final_shared']:
  buckets=defaultdict(list)
  for x in cs:buckets[(x['native'],x['predictions']['rc_initial'],x['predictions'][method])].append(x['node'])
  matrix=[dict(truth=t,initial=a,feedback=b,count=len(ids),nodes=sorted(ids)) for (t,a,b),ids in sorted(buckets.items())]
  totals=dict(resources=len(cs),truth_occupied=sum(x['native'] for x in cs),initial_absolute_error=sum(abs(x['predictions']['rc_initial']-x['native']) for x in cs),feedback_absolute_error=sum(abs(x['predictions'][method]-x['native']) for x in cs),improved_nodes=sum(abs(x['predictions'][method]-x['native'])<abs(x['predictions']['rc_initial']-x['native']) for x in cs),worsened_nodes=sum(abs(x['predictions'][method]-x['native'])>abs(x['predictions']['rc_initial']-x['native']) for x in cs),improvement_units=sum(max(0,abs(x['predictions']['rc_initial']-x['native'])-abs(x['predictions'][method]-x['native'])) for x in cs),worsening_units=sum(max(0,abs(x['predictions'][method]-x['native'])-abs(x['predictions']['rc_initial']-x['native'])) for x in cs),removed_true_occupancy=sum(x['native']==1 and x['predictions']['rc_initial']>0 and x['predictions'][method]==0 for x in cs),added_false_occupancy=sum(x['native']==0 and x['predictions']['rc_initial']==0 and x['predictions'][method]>0 for x in cs),removed_false_occupancy=sum(x['native']==0 and x['predictions']['rc_initial']>0 and x['predictions'][method]==0 for x in cs),added_true_occupancy=sum(x['native']==1 and x['predictions']['rc_initial']==0 and x['predictions'][method]>0 for x in cs))
  assert totals['feedback_absolute_error']-totals['initial_absolute_error']==totals['worsening_units']-totals['improvement_units']
  rows.append(dict(case=case,method=method,totals=totals,matrix=matrix));print(case,method,totals,flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='All original positive-capacity CHANs for original and second swapped exposed SHA; fixed two feedback rounds. Exact occupancy/error transitions, no selected subset, parameter changes, causal/heldout/failure/hardware or timegain proof.'),indent=2)+'\n')
