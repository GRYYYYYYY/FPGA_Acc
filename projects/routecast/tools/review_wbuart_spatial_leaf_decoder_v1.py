"""Second metric implementation and gate reconstruction for all9 cases."""
import json
from pathlib import Path
from prediction_metrics import compare
from verify_wbuart_best_support_ranking_v1 import normalize
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_spatial_leaf_decoder_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def gate(a,b):
 conditions=[];strict=[]
 for scope in ['resource','spatial']:
  x,y=a[scope],b[scope];valid=x['rho'] is not None and y['rho'] is not None
  conditions.extend([valid and x['rho']>=y['rho']-1e-12,x['hits']>=y['hits']]);strict.extend([valid and x['rho']>y['rho']+1e-12,x['hits']>y['hits']])
 return all(conditions) and any(strict)
def main():
 qp=D/'quality_evaluation_v1.json';v=read(qp);assert all(sha(p)==h for p,h in v['bindings'].items());pred=read(D/'predictions_frozen.json')['rows'];base=read(E/'wbuart_paired_bbox_cart_half_v1_2026-10-20/predictions_frozen.json')['rows'];specs=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons'];vectors=0;decomposition={}
 for row in v['rows']:
  case=row['case'];r=next(x for x in pred if x['case']==case);b=next(x for x in base if x['case']==case and x['mode']=='main');s=read(next(x['specification'] for x in specs if x['case']==case));directory=Path(s['domain_proof']).parent;resources=list(map(json.loads,(directory/'resources.jsonl').read_text().splitlines()));bins=read(directory/'spatial_bins.json');domain=read(s['domain_proof']);ids=read(r['resource_ids']);truth=normalize(resources,bins,{int(k):val for k,val in read(s['label_physical_audit'])['node_occupancy'].items()});inputs={'candidate':dict(zip(ids,read(r['point_counts']))),'same_tree_half':dict(zip(ids,read(b['point_counts']))),'previous_native':{int(k):val for k,val in read(s['source_frame'])['ledger'].items()},'original_H0_raw_min_on':{int(k):val for k,val in read(s['predictions']['raw_min_on']['frame'])['ledger'].items()}};metrics={}
  for name,counts in inputs.items():
   values=normalize(resources,bins,counts);metrics[name]={}
   for scope in ['resource','spatial']:
    k=domain[scope+'_k'];m=compare(values[scope],truth[scope],k);got=row['metrics'][name][scope];hits=round(m['precision_at_k']*k);assert hits==got['hits'] and got['k']==k and abs(m['spearman']-got['rho'])<=1e-12;metrics[name][scope]={'rho':m['spearman'],'hits':hits};vectors+=1
  checks={name:gate(metrics['candidate'],metrics[name]) for name in ['previous_native','original_H0_raw_min_on']};assert checks==row['comparisons'] and all(checks.values())==row['both_original_comparisons'];assert all(gate(metrics['same_tree_half'],metrics[name]) for name in checks)==row['same_tree_half_original_gate']
  for control in ['previous_native','original_H0_raw_min_on','same_tree_half']:
   for scope in ['resource','spatial']:
    for metric in ['rho','hits']:
     delta=metrics['candidate'][scope][metric]-metrics[control][scope][metric];eps=1e-12 if metric=='rho' else 0;key=control+'/'+scope+'/'+metric;bucket=decomposition.setdefault(key,{'improved':0,'tied':0,'regressed':0});bucket['improved' if delta>eps else 'regressed' if delta < -eps else 'tied']+=1
 count=sum(r['both_original_comparisons'] for r in v['rows']);assert count==v['candidate_pass'];out=D/'research_review_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL9_ORIGINAL_GATES_AND72_METRIC_VECTORS_INDEPENDENTLY_VERIFIED','metric_vectors':vectors,'candidate_pass':count,'same_tree_half_pass':v['same_tree_half_pass'],'decomposition':decomposition,'promoted':False,'bindings':{str(p):sha(p) for p in [qp,Path(__file__),R/'tools/prediction_metrics.py',R/'tools/verify_wbuart_best_support_ranking_v1.py']},'scope':'Exposed-family surrogate diagnostic only. Original all9, native and fullpaid gates remain required.'},indent=2)+'\n');print('INDEPENDENT_QUALITY_REVIEW_PASS',count,v['same_tree_half_pass'],vectors)
if __name__=='__main__':main()
