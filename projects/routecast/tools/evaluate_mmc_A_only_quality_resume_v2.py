"""Score frozen feasible A-only candidates, retaining all3 capacity outcomes."""
import json,time,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from fractions import Fraction
from pre_route_endpoints import sha
from prediction_metrics import compare
from verify_MMC_complete_static_criticality_metrics_v2_2026_10_19 import verify_metric
R=Path(__file__).resolve().parents[1];S=R/'experiments/mmc_A_only_joint_CBS_resume_v2_2026-10-21';V=S/'verification.json';A=S/'independent_verification_v1.json';v=json.loads(V.read_text());a=json.loads(A.read_text());assert all(sha(p)==h for p,h in a['bindings'].items());assert all(sha(p)==h for k in ['bindings','files'] for p,h in v[k].items());P=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(P.read_text());graph=next(Path(p) for p in v['bindings'] if p.endswith('.xml'));D=R/'experiments/mmc_A_only_quality_resume_v2_2026-10-21';D.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [V,A,P,graph,Path(__file__),R/'tools/prediction_metrics.py',R/'tools/verify_MMC_complete_static_criticality_metrics_v2_2026_10_19.py']};predictions={}
for row in a['rows']:
 case=row['case']
 if row['full_capacity_feasible_states']!=1:continue
 mp=S/(case+'_full_candidate_v1.json');manifest=json.loads(mp.read_text());assert manifest['producer_verification_sha256']==sha(V) and manifest['all_original_model_budgets_verified'] and manifest['overused_CHANNELs']==0;lp=Path(manifest['CHANNEL_ledger']);assert sha(lp)==manifest['CHANNEL_ledger_sha256'];state=json.loads(Path(manifest['source_assessment']).read_text());assert state['full_CHANNEL_capacity_feasible'] and state['trees']==manifest['repaired_tree_paths'];predictions[case]={int(n):value for n,value in json.loads(lp.read_text()).items()};bindings.update({str(p):sha(p) for p in [mp,lp]})
inherited_quality=R/'experiments/mmc_A_only_quality_v1_2026-10-21/results.json';iq=json.loads(inherited_quality.read_text());assert all(sha(p)==h for p,h in iq['bindings'].items());inherited_row=next(r for r in iq['rows'] if r['case']=='case_01');assert inherited_row['necessary_case_gate_pass'];bindings[str(inherited_quality)]=sha(inherited_quality);inherited_capacity=next(r for r in iq['capacity_outcomes'] if r['case']=='case_01')
(D/'protocol.json').write_text(json.dumps({'frozen_capacity_outcomes':[inherited_capacity]+a['rows'],'candidate_bindings':bindings,'scoring':'Feasible candidates only, full concrete and spatial domains K12936/20. Original four metrics and previous_native/raw_min_on necessary comparisons, no label-guided changes. Infeasible or unfinished cases cannot be dropped from full-cohort verdict.','scope':'Exposed development layouts, no full9/unseen/native utility acceptance.'},indent=2)+'\n');start=time.perf_counter();channels={};bins=Counter();stack=[]
for event,e in ET.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
  cap=int(e.get('capacity'))
  if e.get('type') in ['CHANX','CHANY'] and cap>0:
   loc,segment=e.find('loc'),e.find('segment');keys=[(int(loc.get('layer',0)),x,y,e.get('type'),int(segment.get('segment_id')) if segment is not None else -1) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)];channels[int(e.get('id'))]=(cap,keys)
   for key in keys:bins[key]+=cap
  stack[-2].remove(e);e.clear()
 if e.tag=='rr_nodes':break
 stack.pop()
assert len(channels)==258720 and len(bins)==17160;rows=[]
for case,ledger in sorted(predictions.items()):
 assert all(ledger.get(n,0)<=cap for n,(cap,keys) in channels.items());item=next(r for r in plan['cases'] if r['case']==case);label=Path(item['native_label']);truth={int(n):value for n,value in json.loads(label.read_text())['node_occupancy'].items()};quality=Path(item['quality_reference_protocol']).with_name('comparison.json');proof=quality.with_name('verification.json');vp=json.loads(proof.read_text());assert vp['status']=='pass' and vp['bindings'][str(quality)]==sha(quality);prior=json.loads(quality.read_text());assert prior['bindings'][str(label)]==sha(label);sp,st=Counter(),Counter()
 for n,(cap,keys) in channels.items():
  assert truth.get(n,0)<=cap
  for key in keys:sp[key]+=ledger.get(n,0);st[key]+=truth.get(n,0)
 vectors={'concrete':({n:Fraction(ledger.get(n,0),cap) for n,(cap,keys) in channels.items()},{n:Fraction(truth.get(n,0),cap) for n,(cap,keys) in channels.items()},12936),'spatial':({key:Fraction(sp[key],cap) for key,cap in bins.items()},{key:Fraction(st[key],cap) for key,cap in bins.items()},20)};metrics={}
 for scope,(prediction,target,k) in vectors.items():metrics[scope]=compare(prediction,target,k);verify_metric(prediction,target,k,metrics[scope])
 comparisons={}
 for control in ['previous_native','raw_min_on']:
  checks=[]
  for scope in vectors:
   for metric in ['spearman','precision_at_k']:
    candidate=metrics[scope][metric];reference=prior['metrics']['cold'][control][scope][metric];eps=1e-12 if metric=='spearman' else 0;checks.append(dict(scope=scope,metric=metric,candidate=candidate,reference=reference,nonregression=candidate is not None and reference is not None and candidate>=reference-eps,strict=candidate is not None and reference is not None and candidate>reference+eps))
  comparisons[control]={'checks':checks,'necessary_comparison_pass':all(c['nonregression'] for c in checks) and any(c['strict'] for c in checks)}
 rows.append(dict(case=case,metrics=metrics,comparisons=comparisons,necessary_case_gate_pass=all(c['necessary_comparison_pass'] for c in comparisons.values())));bindings.update({str(p):sha(p) for p in [label,quality,proof]});print('A_ONLY_QUALITY',case,{k:c['necessary_comparison_pass'] for k,c in comparisons.items()},flush=True)
rows.insert(0,dict(inherited_row,inherited_from=str(inherited_quality)));all3capacity=len(predictions)+1==3;assert set(predictions)=={r['case'] for r in a['rows'] if r['full_capacity_feasible_states']==1};bindings[str(D/'protocol.json')]=sha(D/'protocol.json');assert all(sha(p)==h for p,h in bindings.items());out={'status':'A_ONLY_FROZEN_FEASIBLE_CANDIDATES_COLD_SCORED_ALL3_OUTCOMES_RETAINED','capacity_outcomes':[inherited_capacity]+a['rows'],'rows':rows,'all3_capacity_pass':all3capacity,'all3_necessary_quality_pass':all3capacity and all(r['necessary_case_gate_pass'] for r in rows),'original_full9_gate_pass':False,'strict_unseen':0,'cost_acceptable_candidate_proven':False,'seconds':time.perf_counter()-start,'independent_numerical_crosscheck':'Both metric vectors per feasible case crosschecked by independent histogram-rank/topK/MAE implementation in evaluator process.','bindings':bindings,'scope':'One bounded A-only development pilot, no full9, matched complete runtime, native/canonical/STA or unseen promotion.'};(D/'results.json').write_text(json.dumps(out,indent=2,default=lambda x:str(x) if isinstance(x,Fraction) else None)+'\n')
