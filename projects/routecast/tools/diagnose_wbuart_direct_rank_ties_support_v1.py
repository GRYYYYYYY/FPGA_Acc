"""Frozen leaf support and optimistic tie sensitivity, all27 case/fold pairs."""
import json
from array import array
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from topk_tie_interval_v1 import interval
from verify_wbuart_best_support_ranking_v1 import normalize
from prediction_metrics import compare
from diagnose_wbuart_best_support_ranking_v1 import numeric_comparison
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_direct_rank_ties_support_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_direct_rank_tree_v1_2026-10-20';qp=source/'quality_evaluation_v1.json';tp=E/'wbuart_direct_rank_training_gap_v1_2026-10-20/verification.json';quality=read(qp);training=read(tp)
 for v in [quality,training]:assert all(sha(p)==h for p,h in v['bindings'].items())
 fp=E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json';wp=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';features={r['case']:r for r in read(fp)['rows']};specs={r['case']:r['specification'] for r in read(wp)['comparisons']};members=[];bindings={};models={}
 def bind(p):bindings[str(p)]=sha(p)
 for p in [Path(__file__),qp,tp,fp,wp,R/'tools/topk_tie_interval_v1.py',R/'tools/verify_wbuart_best_support_ranking_v1.py',R/'tools/prediction_metrics.py',E/'topk_tie_interval_contract_v1_2026-10-20/verification.json']:bind(p)
 # First freeze all memberships using features/model only, before label joins.
 for ep in ['episode_01','episode_02','episode_03']:
  mp=source/ep/'model.json';model=read(mp);models[ep]=model;bind(mp)
  for case in model['training_cases']+model['test_cases']:
   f=features[case];ids=read(f['resource_ids']);a=array('d');a.frombytes(Path(f['matrix']).read_bytes());assigned=[]
   for i in range(len(ids)):
    node=0
    while model['nodes'][node]['feature']>=0:
     n=model['nodes'][node];node=n['left'] if a[i*41+n['feature']]<=n['threshold'] else n['right']
    assigned.append(node)
   # Independent recursive partition filtering, instead of point traversal.
   other=[-1]*len(ids)
   def scatter(node,indices):
    n=model['nodes'][node]
    if n['feature']<0:
     for i in indices:assert other[i]==-1;other[i]=node
    else:
     scatter(n['left'],[i for i in indices if a[i*41+n['feature']]<=n['threshold']]);scatter(n['right'],[i for i in indices if a[i*41+n['feature']]>n['threshold']])
   scatter(0,list(range(len(ids))));assert assigned==other;out=D/ep/case;out.mkdir(parents=True);p=out/'leaf_indices.json';p.write_text(json.dumps(assigned)+'\n');bind(p);bind(f['matrix']);bind(f['resource_ids']);members.append({'fold':ep,'case':case,'role':'train' if case in model['training_cases'] else 'heldout','leaf_indices':str(p),'resource_ids':f['resource_ids']})
 (D/'memberships_frozen.json').write_text(json.dumps({'status':'ALL27_SOURCE_ONLY_MEMBERSHIPS_FROZEN_BEFORE_LABEL_JOIN','rows':members,'target_labels_loaded':False,'bindings':bindings},indent=2)+'\n');rows=[];leaf_tables={}
 for r in members:
  ep,case=r['fold'],r['case'];model=models[ep];ids=read(r['resource_ids']);leaves=read(r['leaf_indices']);sp=specs[case];s=read(sp);directory=Path(s['domain_proof']).parent;rp=directory/'resources.jsonl';bp=directory/'spatial_bins.json';resources=list(map(json.loads,rp.read_text().splitlines()));bins=read(bp);truthp=s['label_physical_audit'];truthcounts={int(k):v for k,v in read(truthp)['node_occupancy'].items()};points={rid:model['nodes'][leaf]['state'] for rid,leaf in zip(ids,leaves)};pred=normalize(resources,bins,points);truth=normalize(resources,bins,truthcounts);old=next(x for x in (training['rows'] if r['role']=='train' else quality['rows']) if x['case']==case and (r['role']!='train' or x['fold']==ep));metrics=old['metrics']['candidate'];bounds={};optimistic={}
  for scope in ['resource','spatial']:
   k=metrics[scope]['k'];b=interval(pred[scope],truth[scope],k);m=compare(pred[scope],truth[scope],k);assert b['actual_ID_hits']==metrics[scope]['hits']==round(m['precision_at_k']*k) and abs(m['spearman']-metrics[scope]['rho'])<=1e-12;bounds[scope]=b;optimistic[scope]={**metrics[scope],'hits':b['maximum_hits']}
  checks={control:numeric_comparison(optimistic,old['metrics'][control]) for control in ['previous_native','original_H0_raw_min_on']};counts=Counter(leaves);positives=Counter()
  for rid,leaf in zip(ids,leaves):positives[leaf]+=truthcounts.get(rid,0)
  leaf_tables[(ep,case)]={leaf:(counts[leaf],positives[leaf]) for leaf in counts};rows.append({**r,'tie_intervals':bounds,'optimistic_independent_scope_checks':checks,'optimistic_both_controls':all(checks.values()),'actual_both_controls':old['both_original_controls'] if r['role']=='train' else old['both_original_controls']['candidate'],'leaf_counts':{str(k):{'n':n,'positive':p} for k,(n,p) in leaf_tables[(ep,case)].items()}})
  for p in [sp,rp,bp,truthp]:bind(p)
  print('TIE_SUPPORT_VERIFIED',ep,case,r['role'],all(checks.values()),flush=True)
 shifts=[]
 for ep,model in models.items():
  pooled=Counter();positive=Counter()
  for case in model['training_cases']:
   for leaf,(n,p) in leaf_tables[(ep,case)].items():pooled[leaf]+=n;positive[leaf]+=p
  for i,node in enumerate(model['nodes']):
   if node['feature']<0:assert pooled[i]==node['rows']
  for r in [x for x in rows if x['fold']==ep]:
   support=leaf_tables[(ep,r['case'])];total=sum(n for n,p in support.values());gap=sum(F(n,total)*abs(F(p,n)-F(positive[k],pooled[k])) for k,(n,p) in support.items());shifts.append({'fold':ep,'case':r['case'],'role':r['role'],'weighted_absolute_leaf_occupancy_rate_gap':float(gap),'rows_in_zero_train_support_leaves':sum(n for k,(n,p) in support.items() if not pooled[k])})
 summary={role:{'pairs':sum(r['role']==role for r in rows),'actual_pass':sum(r['actual_both_controls'] for r in rows if r['role']==role),'optimistic_tie_pass':sum(r['optimistic_both_controls'] for r in rows if r['role']==role)} for role in ['train','heldout']};(D/'verification.json').write_text(json.dumps({'status':'ALL27_MEMBERSHIPS_LEAF_SUPPORT_AND54_TIE_INTERVALS_VERIFIED','rows':rows,'leaf_rate_shifts':shifts,'summary':summary,'bindings':bindings,'scope':'Exact per-scope TopK tie interval, target TopK fixed original IDs. Independent maxima may be jointly unattainable by one shared tie rule; optimistic failure rules out tie-only rescue for this frozen field, optimistic success is not a predictor. Rate shifts use target labels diagnostically, not fit features. No original gate changes or promotion.'},indent=2)+'\n');print('ALL27_TIE_SUPPORT_COMPLETE',summary)
if __name__=='__main__':main()
