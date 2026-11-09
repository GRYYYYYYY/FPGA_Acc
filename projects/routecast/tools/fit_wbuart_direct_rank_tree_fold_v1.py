"""One frozen direct-rank fold; only training-domain labels loaded."""
import json,sys,time
from array import array
from pathlib import Path
from direct_rank_domain_v1 import load_training_domains
from direct_rank_sparse_tree_v1 import train
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def read(p):return json.loads(Path(p).read_text())
def encode(v):
 from fractions import Fraction
 if isinstance(v,Fraction):return {'numerator':v.numerator,'denominator':v.denominator}
 if isinstance(v,dict):return {k:encode(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [encode(x) for x in v]
 return v

def main():
 ep=sys.argv[1];assert ep in ['episode_01','episode_02','episode_03'];D=E/'wbuart_direct_rank_tree_v1_2026-10-20'/ep;D.mkdir(parents=True,exist_ok=False);fp=E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json';wp=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';mp=E/'wbuart_paired_bbox_cart_v1_2026-10-20'/ep/'main/model.json';original=read(mp);features={r['case']:r for r in read(fp)['rows']};specs={r['case']:r['specification'] for r in read(wp)['comparisons']};domains,paths=load_training_domains(R,original,features,specs);X=[];bindings={}
 for case,_ in domains:
  f=features[case];a=array('d');a.frombytes(Path(f['matrix']).read_bytes());assert len(a)==f['rows']*41;X.extend(list(a[i*41:(i+1)*41]) for i in range(f['rows']));paths.extend([f['matrix'],f['resource_ids']])
 for p in [Path(__file__),R/'tools/direct_rank_sparse_tree_v1.py',R/'tools/direct_rank_split_sweep_v1.py',R/'tools/direct_rank_sparse_state_v1.py',R/'tools/direct_rank_domain_v1.py',R/'tools/direct_rank_objective_v1.py',fp,wp,mp,E/'wbuart_direct_rank_partition_design_v1_2026-10-20/protocol.json',E/'direct_rank_sparse_tree_contract_v1_2026-10-20/verification.json',E/'wbuart_direct_rank_split_sweep_contract_v2_2026-10-20/verification.json',*paths]:bindings[str(p)]=sha(p)
 (D/'input_frozen.json').write_text(json.dumps({'status':'TRAINING_INPUTS_FROZEN','training_cases':original['training_cases'],'test_cases':original['test_cases'],'training_rows':len(X),'columns':41,'bindings':bindings,'heldout_labels_loaded':False},indent=2)+'\n');print('DIRECT_RANK_FIT_STARTED',ep,len(X),flush=True);tick=time.perf_counter();model=train(X,domains,depth=8,minleaf=64);model.update(training_cases=original['training_cases'],test_cases=original['test_cases'],columns_count=41,depth_limit=8,minimum_child_rows=64,training_seconds=time.perf_counter()-tick);p=D/'model.json';p.write_text(json.dumps(encode(model),indent=2)+'\n');bindings[str(p)]=sha(p);outputs=[]
 for case in original['test_cases']:
  f=features[case];a=array('d');a.frombytes(Path(f['matrix']).read_bytes());points=[]
  for i in range(f['rows']):
   node=0
   while model['nodes'][node]['feature']>=0:
    n=model['nodes'][node];node=n['left'] if a[i*41+n['feature']]<=n['threshold'] else n['right']
   points.append(model['nodes'][node]['state'])
  p=D/(case.replace('/','_')+'_points.json');p.write_text(json.dumps(points)+'\n');bindings[str(p)]=sha(p)
  for q in [f['matrix'],f['resource_ids']]:bindings[str(q)]=sha(q)
  outputs.append({'case':case,'point_counts':str(p),'resource_ids':f['resource_ids'],'model':str(D/'model.json')})
 (D/'predictions_frozen.json').write_text(json.dumps({'status':'ONE_FOLD_HELDOUT_FIELDS_FROZEN_PENDING_INDEPENDENT_REPLAY','rows':outputs,'heldout_labels_loaded':False,'bindings':bindings},indent=2)+'\n');print('DIRECT_RANK_FOLD_FROZEN',ep,len(model['nodes']),model['training_seconds'],flush=True)
if __name__=='__main__':main()
