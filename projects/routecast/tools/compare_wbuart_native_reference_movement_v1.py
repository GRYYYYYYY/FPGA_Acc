"""Compare source-relative NET channel movements of both native references."""
import sys,json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from native_route_ledger_import_compact import physical_paths
E=R/'experiments';D=E/'wbuart_dual_reference_metrics_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 W=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';seeds=E/'wbuart_target_native_seeds_v1_2026-10-20/verification.json';rows=[];bindings={str(p):sha(p) for p in [Path(__file__),W,seeds]}
 for c in read(W)['comparisons']:
  s=read(c['specification']);ep=read(s['endpoint']);seed=next(x for x in read(seeds)['rows'] if x['case']==c['case']);dirty=set(seed['dirty_NETs']);nameid={name:int(n) for n,name in ep['net_names'].items()};folder=Path(s['domain_proof']).parent;ids={json.loads(x)['id'] for x in (folder/'resources.jsonl').read_text().splitlines()};paths={'source':seed['source_route'],'cold':str(Path(s['label_physical_audit']).parent/'output.route'),'source_restart':str(E/'wbuart_target_source_restart_reference_v1_2026-10-20'/c['case']/'output.route')};supports={}
  for ref,p in paths.items():
   supports[ref]={name:{n for branch in branches for n,sw in branch}&ids for name,branches in physical_paths(Path(p)).items() if branches};bindings[p]=sha(p)
  assert len(supports['source'])==1074 and all(supports[n].keys()==supports['source'].keys() for n in supports);counts=Counter()
  for name,old in supports['source'].items():
   category='dirty' if nameid[name] in dirty else 'endpoint_unchanged';cold=supports['cold'][name];restart=supports['source_restart'][name];counts[category+'/NETs']+=1;counts[category+'/cold_changed_NETs']+=old!=cold;counts[category+'/restart_changed_NETs']+=old!=restart;counts[category+'/cold_source_support_difference']+=len(old^cold);counts[category+'/restart_source_support_difference']+=len(old^restart);counts[category+'/cold_restart_support_difference']+=len(cold^restart)
  rows.append({'case':c['case'],'counts':dict(counts)});print(c['case'],counts['endpoint_unchanged/cold_changed_NETs'],counts['endpoint_unchanged/restart_changed_NETs'],flush=True)
 assert len(rows)==9
 (D/'native_reference_movement_v1.json').write_text(json.dumps({'status':'ALL9_BOTH_NATIVE_REFERENCE_MOVEMENTS_FROM_SOURCE_RECONSTRUCTED','rows':rows,'bindings':bindings,'scope':'One cold and one seeded restart solution per case; solution-specific support movements, not necessity or causal proof. Does not alter forecast metrics/gates.'},indent=2)+'\n')
if __name__=='__main__':main()
