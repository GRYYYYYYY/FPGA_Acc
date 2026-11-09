"""Retrospective stronger repaired baseline; require identical native vectors/universes."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
out=R/'experiments/mcnc_budgeted_soft_demand_v1_2026-10-07';sp=out/'comparison.json';sv=out/'metric_verification.json';soft=json.loads(sp.read_text());proof=json.loads(sv.read_text());assert proof['bindings'][str(sp)]==sha(sp) and proof['histogram_ranks_topk_mae_and_complete_scope_pass'];parent=R/'experiments/mcnc_pending_swap_observer_native_validation_v21_2026-10-07';hp=parent/'receipt.json';hv=parent/'verification.json';hard=json.loads(hp.read_text());verified=json.loads(hv.read_text());assert verified['bindings'][str(hp)]==sha(hp);bindings={**closure([Path(__file__)]),str(sp):sha(sp),str(sv):sha(sv),str(hp):sha(hp),str(hv):sha(hv)};rows=[]
for h in hard['rows']:
 s=next(x for x in soft['rows'] if x['name']==h['name']);name=h['name'];complete=h['completed']==h['required']
 if not complete:rows.append(dict(name=name,hard_complete=False,hard_completed=h['completed'],hard_required=h['required'],hard_metrics=None,soft_metrics=s['metrics']['shared_net'],matched=None));continue
 file=parent/name/'metric_vectors.json';assert sha(file)==h['files'][str(file)]==verified['bindings'][str(file)];bindings[str(file)]=sha(file);d=json.loads(file.read_text());sfile=out/name/'comparison_vectors.json';assert sha(sfile)==soft['bindings'][str(sfile)];bindings[str(sfile)]=sha(sfile);sd=json.loads(sfile.read_text())
 for kind,key in [('channels','node'),('bins','key')]:
  identity=lambda x:tuple(x[key]) if isinstance(x[key],list) else x[key]
  assert {identity(x):(x['capacity'],x['native']) for x in d[kind]}=={identity(x):(x['capacity'],x['native']) for x in sd[kind]}
 metrics={}
 for kind,space,k in [('channels','concrete',max(1,len(d['channels'])//20)),('bins','spatial',20)]:
  key=lambda x:x['node'] if kind=='channels' else tuple(x['key']);m=compare({key(x):x['predicted']/x['capacity'] for x in d[kind]},{key(x):x['native']/x['capacity'] for x in d[kind]},k);assert m==h['metrics'][space];metrics[space]=m
 rows.append(dict(name=name,hard_complete=True,matched=True,hard_metrics=metrics,soft_metrics=s['metrics']['shared_net'],hard_quality_pass=h['quality_pass'],hard_complete_gain_pass=h['complete_gain_pass'],hard_workflow_complete_seconds=h['workflow_complete_seconds'],cold_routing_and_canonical_seconds=h['cold_routing_and_canonical_seconds'],soft_prediction_only_seconds=s['paid_prediction_seconds']))
assert all(sha(k)==h for k,h in bindings.items());(out/'repaired_hard_comparison.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Development retrospective stronger baseline. Matched original native vectors and universes on complete cases only; incomplete hardcase null, not zero. Repaired hard includes archived recovery whereas soft has no legal joint routing; times are different scopes, no netgain claim.'),indent=2)+'\n');print('MATCHED REPAIRED BASELINE',[(x['name'],x.get('hard_metrics',{}).get('spatial',{}).get('precision_at_k') if x['hard_metrics'] else None,x['soft_metrics']['spatial']['precision_at_k']) for x in rows],flush=True)
