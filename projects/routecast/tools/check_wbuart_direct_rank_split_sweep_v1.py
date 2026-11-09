"""One fixed real training subset, full domains, all candidate comparisons."""
import json,time
from array import array
from pathlib import Path
from direct_rank_domain_v1 import load_training_domains,training_objective
from direct_rank_split_sweep_v1 import scan
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def read(p):return json.loads(Path(p).read_text())
def main():
 fp=E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json';wp=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';mp=E/'wbuart_paired_bbox_cart_v1_2026-10-20/episode_01/main/model.json';features={r['case']:r for r in read(fp)['rows']};specs={r['case']:r['specification'] for r in read(wp)['comparisons']};domains,paths=load_training_domains(R,read(mp),features,specs);X=[];members=[];mapping=[];fields=[];bindings={}
 for c,(case,d) in enumerate(domains):
  f=features[case];a=array('d');a.frombytes(Path(f['matrix']).read_bytes());assert len(a)==len(d.ids)*41;offset=len(X);X.extend([a[i*41+1],a[i*41+10]] for i in range(len(d.ids)));members.extend(range(offset,offset+64));mapping.extend((c,i) for i in range(len(d.ids)));fields.append([int(i%3==0) for i in range(len(d.ids))]);paths.append(f['matrix'])
 tick=time.perf_counter();actual=scan(X,domains,fields,members,64,True);sparse_seconds=time.perf_counter()-tick;baseline=training_objective(domains,fields);reference=[];tick=time.perf_counter()
 for f in range(2):
  for threshold in sorted(set(X[i][f] for i in members))[:-1]:
   left=[i for i in members if X[i][f]<=threshold];right=[i for i in members if X[i][f]>threshold]
   if min(len(left),len(right))<64:continue
   for a,b in [(0,0),(0,1),(1,0),(1,1)]:
    proposed=[p.copy() for p in fields]
    for i in left:
     c,j=mapping[i];proposed[c][j]=a
    for i in right:
     c,j=mapping[i];proposed[c][j]=b
    reference.append(((f,threshold,a,b),training_objective(domains,proposed)))
 assert actual['trace']==reference and actual['before']==baseline
 eligible=[(v,key) for key,v in reference if v<baseline];assert (actual['after'],actual['choice'])==(min(eligible) if eligible else (baseline,None))
 D=E/'wbuart_direct_rank_split_sweep_contract_v1_2026-10-20';D.mkdir(exist_ok=False)
 for p in [Path(__file__),R/'tools/direct_rank_split_sweep_v1.py',R/'tools/direct_rank_domain_v1.py',R/'tools/direct_rank_sparse_state_v1.py',fp,wp,mp,*paths,E/'direct_rank_split_sweep_contract_v1_2026-10-20/verification.json']:bindings[str(p)]=sha(p)
 v={'status':'PASS_REAL_TRAIN_SUBSET_ALL_CANDIDATE_FULL_FIELD_EQUIVALENCE','fold':'episode_01','full_training_rows':len(X),'subset_members':len(members),'subset_policy':'First64 sorted resourceIDs in each of six training cases, independent of labels. Two original feature columns1(xlow),10(prior occupancy). Fixed label-free i%3 background. minchild64.','candidate_objectives':len(reference),'sparse_case_score_calls':actual['case_scores'],'sparse_seconds':sparse_seconds,'reference_seconds':time.perf_counter()-tick,'bindings':bindings,'scope':'Fixed partial candidate contract only, not a trained tree, selected predictor, all41-feature performance result or hardware claim.'};assert reference;(D/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'],v['candidate_objectives'],v['sparse_seconds'],v['reference_seconds'])
if __name__=='__main__':main()
