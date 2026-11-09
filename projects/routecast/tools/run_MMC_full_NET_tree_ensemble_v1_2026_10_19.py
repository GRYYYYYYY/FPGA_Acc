"""Complete fixed3-layout known-MMC development ensemble; no route label input."""
import pathlib,json,hashlib,time,resource,os
from collections import defaultdict,Counter
from fractions import Fraction
from shortest_NET_tree_csr_v1 import prepare_csr
from NET_tree_expected_occupancy_v1 import predict,EXACT_ASSIGNMENT_LIMIT,SAMPLES,SEED
from MMC_zero_node_RC_shared_CSR_v1 import load
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,separators=(',',':'));f.write('\n')
def main():
 resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));start=time.perf_counter();I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19';O=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';cases=[f'episode_{i:02d}' for i in range(1,4)];inputs={name:I/name/'demand/endpoints.json' for name in cases};metas={name:json.loads(p.read_text()) for name,p in inputs.items()};graph=pathlib.Path(metas[cases[0]]['inputs']['graph']['path']);assert all(meta['graph_sha256']==sha(graph) for meta in metas.values());files=[pathlib.Path(__file__).resolve(),graph,*inputs.values(),R/'tools/NET_tree_expected_occupancy_v1.py',R/'tools/exact_NET_tree_expectation_v1.py',R/'tools/shortest_NET_tree_ensemble_v1.py',R/'tools/shortest_NET_tree_csr_v1.py',R/'tools/MMC_zero_node_RC_shared_CSR_v1.py',R/'experiments/NET_tree_expected_occupancy_core_v1_2026-10-19/verification.json',R/'experiments/mmc_NET_tree_csr_certified_batch_v2_2026-10-19/independent_global_dual_verification_v1.json'];bindings={str(p):sha(p) for p in files};O.mkdir()
 write(O/'protocol.json',dict(bindings=bindings,cases=cases,required_connections_each=115572,required_NETs_each=55300,exact_assignment_limit=EXACT_ASSIGNMENT_LIMIT,samples=SAMPLES,seed=SEED,cache_key='NET id, source, sorted distinct sinks; exact match only',policy='Exact additive RC minimum then minimum hops; shared parent tree ensemble. Single sink exact DP; multi sink <=4096 local-parent assignments exact; other multi sink16samples seed19. No costs/parameters depend on native target labels.',evaluation='Known exposed development layouts only. Primary future post-iteration1 sum pressure: tie-averaged top5percent captured mass and Spearman; nonregress both and strict>=1 vs each raw_min,previous_native,native_retained control in all3cases. Uniform strict capture>5percent only. Undefined candidate or nonuniform control rho =>unassessable. epsilon1e-12. Original cold gates unchanged; no posthoc case/metric/model replacement.',scope='Full-design software demand predictor production, not legal routing. No target route label reads, STA/hardware, strict unseen family or fullworkflow timing claim. Full global dual coverage and independent prediction audit pending.'))
 offsets,dest,costs,caps,kinds,setup_seconds=load(graph);print('SHARED GRAPH READY',setup_seconds,flush=True);cache={};cache_indices={};rows=[];unique=0
 with (O/'NET_contributions.jsonl').open('x') as journal:
  for name in cases:
   case_start=time.perf_counter();groups=defaultdict(list)
   for q in metas[name]['connections']:groups[q['net_id']].append(q)
   assert len(metas[name]['connections'])==115572 and len(groups)==55300;ledger=Counter();modes=Counter();hits=0;search_seconds=0;expectation_seconds=0;index=[]
   for ordinal,(net,qs) in enumerate(sorted(groups.items()),1):
    sources={q['source'] for q in qs};assert len(sources)==1;source=sources.pop();sinks=tuple(sorted({q['sink'] for q in qs}));key=(net,source,sinks)
    if key in cache:prediction=cache[key];hits+=1
    else:
     tick=time.perf_counter();prepared=prepare_csr(offsets,dest,costs,caps,kinds,source,sinks);search_seconds+=time.perf_counter()-tick;tick=time.perf_counter();prediction=predict(prepared,net_id=net);expectation_seconds+=time.perf_counter()-tick;cache[key]=prediction;cache_indices[key]=unique
     record=dict(index=unique,first_case=name,net_id=net,source=source,sinks=sinks,mode=prediction['mode'],probabilities={str(n):str(x) for n,x in prediction['probabilities'].items()},support_choices={str(n):list(x) for n,x in prepared['choices'].items()},support_distance={str(n):list(x) for n,x in prepared['distance'].items()},search_stats=prepared['search_stats']);journal.write(json.dumps(record,separators=(',',':'))+'\n');unique+=1
    assert prediction['probabilities'][source]==1 and all(0<x<=1 for x in prediction['probabilities'].values());ledger.update(prediction['probabilities']);modes[prediction['mode']]+=1;index.append(cache_indices[key])
    if ordinal%1000==0:
     journal.flush();status=dict(case=name,completed_NETs=ordinal,required_NETs=55300,unique_NET_endpoint_sets=unique,cache_hits=hits,modes=dict(modes),elapsed_seconds=time.perf_counter()-start);tmp=O/'progress.tmp';tmp.write_text(json.dumps(status));os.replace(tmp,O/'progress.json');print('PROGRESS',name,ordinal,'cache',hits,'elapsed',round(status['elapsed_seconds'],2),flush=True)
   assert len(index)==55300 and all(x>=0 for x in ledger.values());d=O/name;d.mkdir();write(d/'NET_contribution_indices.json',index);write(d/'expected_unique_NET_occupancy.json',{str(n):str(x) for n,x in sorted(ledger.items())});row=dict(case=name,connections=115572,NETs=55300,cache_hits=hits,new_endpoint_sets=55300-hits,modes=dict(modes),search_seconds=search_seconds,expectation_seconds=expectation_seconds,component_seconds=time.perf_counter()-case_start);rows.append(row);write(d/'receipt.json',row);print('CASE COMPLETE',name,row,flush=True)
 for p,h in bindings.items():assert sha(p)==h,p
 for p in O.rglob('*'):
  if p.is_file():bindings[str(p)]=sha(p)
 write(O/'receipt.json',dict(status='ALL3_COMPLETE_55300_NET_ENSEMBLE_PREDICTIONS_PRODUCED',bindings=bindings,rows=rows,unique_NET_endpoint_sets=unique,graph_setup_seconds=setup_seconds,paid_component_seconds=time.perf_counter()-start,independent_prediction_audit_pending=True,forecast_quality_pending=True,scope='Complete known-family development predictions; no native target labels read. Fractional expected uniqueNET demand, not legal multiNET routing, full_STA/minimum_dual/hardware or net-time gain.'))
if __name__=='__main__':main()
