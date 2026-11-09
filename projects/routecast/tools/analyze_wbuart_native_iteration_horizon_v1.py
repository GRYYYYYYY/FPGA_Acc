"""Reconstruct every complete native iteration checkpoint against its own final."""
import json,hashlib
from pathlib import Path
from collections import Counter
from fractions import Fraction
from external_forecast_metrics_v1 import vectors,metrics,gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_native_iteration_horizon_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def checkpoints(path):
 with Path(path).open() as f:
  assert next(f)=='TRACE 1\n'
  for line in f:
   w=line.split()
   if not w or w[0]!='CP':continue
   tag,it=w[1],int(w[2]);ledger=Counter();nets=set()
   for line in f:
    z=line.split()
    if z==['CE']:break
    if z[0]!='T':continue
    net,ignored,present,remaining,count=map(int,z[1:6]);nodes=list(map(int,z[6:]));assert net not in nets and len(nodes)==count and len(set(nodes))==count;nets.add(net)
    if present and not ignored:ledger.update(nodes)
   yield tag,it,dict(ledger)
def main():
 D.mkdir(exist_ok=False);W=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';bindings={str(p):sha(p) for p in [Path(__file__),W]};rows=[];total=0
 for c in read(W)['comparisons']:
  spec=read(c['specification']);domain=read(spec['domain_proof']);folder=Path(spec['domain_proof']).parent;resources=[json.loads(l) for l in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');source={int(n):v for n,v in read(spec['source_frame'])['ledger'].items()};sv=vectors(resources,bins,source,domain['graph_nodes']);paths={'cold':E/'wbuart_native_evaluation_v1_2026-10-20/utility'/c['case']/'disabled','source_restart':E/'wbuart_target_source_restart_reference_v1_2026-10-20'/c['case']}
  for ref,out in paths.items():
   
   if ref=='cold':assert sha(out/'output.route')==sha(Path(spec['label_physical_audit']).parent/'output.route')
   proof=read(out/'verification.json');assert proof['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and proof['independent_trace_replay_pass'];assert all(sha(p)==h for p,h in proof['bindings'].items());target={int(n):v for n,v in read(out/'physical_audit.json')['node_occupancy'].items()};tv=vectors(resources,bins,target,domain['graph_nodes'],truth=True);source_metrics=metrics(sv,tv,domain['resource_k'],domain['spatial_k']);stages=[];iterations=[]
   for tag,it,ledger in checkpoints(out/'owner_trace.tsv'):
    if tag not in ['initial','iteration_end_after_local_opins','final_after_best_restore']:continue
    m=metrics(vectors(resources,bins,ledger,domain['graph_nodes']),tv,domain['resource_k'],domain['spatial_k']);small={s:{k:v for k,v in x.items() if k in ['spearman','top_k_hits','k','universe_size']} for s,x in m.items()};stages.append({'tag':tag,'iteration':it,'ledger':ledger,'metrics':small,'same_rule_vs_source':gate(m,source_metrics),'CHANNEL_occupancy_L1_error':sum(abs(ledger.get(r['id'],0)-target.get(r['id'],0)) for r in resources)})
    if tag=='iteration_end_after_local_opins':iterations.append(it)
    if tag=='final_after_best_restore':assert ledger==target
   assert iterations==list(range(1,proof['iterations']+1)) and stages[-1]['tag']=='final_after_best_restore';total+=len(stages);rows.append({'case':c['case'],'reference':ref,'native_verification':str(out/'verification.json'),'domain_proof':spec['domain_proof'],'label_physical_audit':str(out/'physical_audit.json'),'source_frame':spec['source_frame'],'source_metrics':source_metrics,'stages':stages});bindings[str(out/'verification.json')]=sha(out/'verification.json');print(c['case'],ref,[(s['iteration'],s['same_rule_vs_source']['pass_primary_gate']) for s in stages if s['tag']=='iteration_end_after_local_opins' and s['iteration']<=2],flush=True)
 assert len(rows)==18
 (D/'verification.json').write_text(json.dumps({'status':'ALL18_NATIVE_FULL_ITERATION_TRAJECTORIES_RECONSTRUCTED','rows':rows,'stages':total,'bindings':bindings,'scope':'Native intermediate state versus its own final solution, fixed first-two snapshots and complete trajectories. Original source-relative rule diagnostic only, not forecast-vs-raw acceptance or new policy. Full paid native prefix cost not comparable to forecast component time.'},indent=2,default=lambda x:{'numerator':x.numerator,'denominator':x.denominator} if isinstance(x,Fraction) else None)+'\n')
if __name__=='__main__':main()
