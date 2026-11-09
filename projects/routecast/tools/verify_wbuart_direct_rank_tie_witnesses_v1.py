"""Construct per-scope extreme TopK witnesses, without interval formula."""
import json
from pathlib import Path
from verify_wbuart_best_support_ranking_v1 import normalize
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_direct_rank_ties_support_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 source=D/'verification.json';v=read(source);assert all(sha(p)==h for p,h in v['bindings'].items());specs={r['case']:r['specification'] for r in read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons']};witnesses=[]
 for r in v['rows']:
  model=read(E/'wbuart_direct_rank_tree_v1_2026-10-20'/r['fold']/'model.json');ids=read(r['resource_ids']);leaves=read(r['leaf_indices']);s=read(specs[r['case']]);directory=Path(s['domain_proof']).parent;resources=list(map(json.loads,(directory/'resources.jsonl').read_text().splitlines()));bins=read(directory/'spatial_bins.json');pred=normalize(resources,bins,{i:model['nodes'][leaf]['state'] for i,leaf in zip(ids,leaves)});truth=normalize(resources,bins,{int(k):val for k,val in read(s['label_physical_audit'])['node_occupancy'].items()})
  for scope in ['resource','spatial']:
   value=r['tie_intervals'][scope]
   # K comes from original domain, not from the claimed interval metadata.
   domain=read(s['domain_proof']);k=domain[scope+'_k'];target=set(sorted(truth[scope],key=lambda key:(-truth[scope][key],key))[:k]);a=pred[scope];cut=sorted(a.values(),reverse=True)[k-1];strict={key for key in a if a[key]>cut};boundary={key for key in a if a[key]==cut};needed=k-len(strict)
   low=sorted(boundary,key=lambda key:(key in target,key))[:needed];high=sorted(boundary,key=lambda key:(key not in target,key))[:needed];lo=len((strict|set(low))&target);hi=len((strict|set(high))&target);assert lo==value['minimum_hits'] and hi==value['maximum_hits'] and len(strict|set(low))==len(strict|set(high))==k
   witnesses.append({'fold':r['fold'],'case':r['case'],'role':r['role'],'scope':scope,'minimum_hits':lo,'maximum_hits':hi,'min_boundary_keys':low,'max_boundary_keys':high})
 assert len(witnesses)==54
 p=D/'independent_witness_verification_v1.json';assert not p.exists();p.write_text(json.dumps({'status':'ALL54_TIE_INTERVAL_EXTREMES_CONSTRUCTIVELY_VERIFIED','witnesses':witnesses,'bindings':{str(q):sha(q) for q in [source,Path(__file__),R/'tools/verify_wbuart_best_support_ranking_v1.py']},'scope':'Explicit per-scope target-dependent witnesses; no single joint tie rule or admitted predictor. Original IDs/gates unchanged.'},indent=2)+'\n');print('ALL54_CONSTRUCTIVE_TIE_WITNESSES_VERIFIED')
if __name__=='__main__':main()
