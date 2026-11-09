"""Real six-case folds: independent original normalization/rank checks."""
import json
from pathlib import Path
from direct_rank_domain_v1 import load_training_domains, training_objective
from verify_wbuart_best_support_ranking_v1 import normalize
from prediction_metrics import compare
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_direct_rank_domain_contract_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);fp=E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json';wp=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';features={r['case']:r for r in read(fp)['rows']};specs={r['case']:r['specification'] for r in read(wp)['comparisons']};bindings={};rows=[];vectors=0
 def bind(p):bindings[str(p)]=sha(p)
 for p in [Path(__file__),R/'tools/direct_rank_domain_v1.py',R/'tools/direct_rank_objective_v1.py',R/'tools/prediction_metrics.py',R/'tools/verify_wbuart_best_support_ranking_v1.py',fp,wp,E/'wbuart_direct_rank_partition_design_v1_2026-10-20/protocol.json']:bind(p)
 for ep in ['episode_01','episode_02','episode_03']:
  mp=E/'wbuart_paired_bbox_cart_v1_2026-10-20'/ep/'main/model.json';model=read(mp);domains,paths=load_training_domains(R,model,features,specs);assert [case for case,_ in domains]==model['training_cases'];assert not set(model['test_cases'])&{case for case,_ in domains}
  for p in [mp,*paths]:bind(p)
  for case,obj in domains:
   s=read(specs[case]);directory=Path(s['domain_proof']).parent;resources=list(map(json.loads,(directory/'resources.jsonl').read_text().splitlines()));bins=read(directory/'spatial_bins.json');truthcounts={int(k):v for k,v in read(s['label_physical_audit'])['node_occupancy'].items()};truth=normalize(resources,bins,truthcounts);tests=[[0]*len(obj.ids),[1]*len(obj.ids),[int(i%3==0) for i in range(len(obj.ids))],[truthcounts.get(i,0) for i in obj.ids]]
   for field in tests:
    actual=obj.score(field);values=normalize(resources,bins,dict(zip(obj.ids,field)))
    for i,(scope,k) in enumerate([('resource',obj.rk),('spatial',obj.sk)]):
     m=compare(values[scope],truth[scope],k);rho=m['spearman'];assert (rho is None and actual[2*i]==-2) or rho is not None and abs(float(actual[2*i])-rho*abs(rho))<=1e-12;assert abs(float(actual[2*i+1])-m['precision_at_k'])<=1e-15;vectors+=1
   for ci,path in enumerate([s['source_frame'],s['predictions']['raw_min_on']['frame']]):
    values=normalize(resources,bins,{int(k):v for k,v in read(path)['ledger'].items()})
    for i,(scope,k) in enumerate([('resource',obj.rk),('spatial',obj.sk)]):
     m=compare(values[scope],truth[scope],k);rho=m['spearman'];actual=obj.controls[ci];assert (rho is None and actual[2*i]==-2) or rho is not None and abs(float(actual[2*i])-rho*abs(rho))<=1e-12;assert abs(float(actual[2*i+1])-m['precision_at_k'])<=1e-15;vectors+=1
   rows.append({'fold':ep,'case':case,'resources':len(obj.ids),'bins':len(obj.bin_keys),'stress_fields':4});print('REAL_TRAIN_DOMAIN_PASS',ep,case,flush=True)
  perfect=[[y for y in obj.truth] for _,obj in domains];value=training_objective(domains,perfect);assert value[0]==0 and value[1]==0 and value[2]==0
 assert len(rows)==18 and vectors==216
 (D/'verification.json').write_text(json.dumps({'status':'PASS_ALL18_TRAIN_DOMAINS_AND216_METRIC_VECTORS','rows':rows,'metric_vectors':vectors,'bindings':bindings,'scope':'Target truth used as score stress test only; no model fit or deployable perfect prediction. Unit capacity binary domain only. Cached resource exact formula and native spatial scatter verified; scalable split scorer not yet implemented.'},indent=2)+'\n');print('ALL18_REAL_DOMAINS_QUALIFIED',vectors)
if __name__=='__main__':main()
