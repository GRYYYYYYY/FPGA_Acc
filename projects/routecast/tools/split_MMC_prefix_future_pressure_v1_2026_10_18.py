"""Fixed iteration1 boundary on exposed traces; no training or quality promotion."""
import pathlib,json,hashlib
from collections import Counter
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def main():
 out=R/'experiments/mmc_prefix_future_pressure_split_v1_2026-10-18';out.mkdir();existing=R/'experiments/mmc_checkpoint_pressure_targets_v1_2026-10-18';proof=existing/'independent_verification_v1.json';v=json.loads(proof.read_text());assert v['status']=='pass';bindings={str(pathlib.Path(__file__).resolve()):sha(__file__),str(proof):sha(proof)};cases=[(c,p) for c in ['case_01','case_02','case_03'] for p in ['off','on']]
 for case,policy in cases:
  p=existing/f'{case}_{policy}.json';assert v['bindings'][str(p)]==sha(p);bindings[str(p)]=sha(p)
 protocol=dict(bindings=bindings,cutoff_iteration=1,phase='iteration_end_after_local_opins',feature='Sparse overflow units at the first complete designated checkpoint only; zero means no sampled overflow, not zero occupancy.',targets='PerRR peak, sum and frequency over complete designated checkpoints2throughterminal, excluding checkpoint1.',scope='All6 already exposed partial-seed runs. Diagnostic temporal data separation only; not placement-only input, new-family validation, predictor training or changed cold gate. Prefix execution cost remains chargeable.')
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for case,policy in cases:
  full=json.loads((existing/f'{case}_{policy}.json').read_text());trace=R/f'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18/{case}/{policy}/owner_trace.tsv';assert sha(trace)==full['source_trace_sha256'];selected=False;first=None;peak=Counter();area=Counter();frequency=Counter();checkpoint=[];current={};first_end=None
  with trace.open('rb') as f:
   for line in f:
    if line.startswith(b'CP '):
     _,phase,i=line.split();selected=phase==b'iteration_end_after_local_opins';iteration=int(i);current={};continue
    if selected and line.startswith(b'V '):
     _,n,occupancy,capacity=line.split();n=int(n);occupancy=int(occupancy);capacity=int(capacity);assert 0<=n<full['RR_domain_size'] and n not in current and occupancy>capacity;current[n]=occupancy-capacity
    if selected and line.strip()==b'CE':
     assert iteration==len(checkpoint)+1;checkpoint.append(iteration)
     if iteration==1:first=current.copy();first_end=f.tell()
     else:
      for n,x in current.items():peak[n]=max(peak[n],x);area[n]+=x;frequency[n]+=1
     selected=False
  assert first is not None and checkpoint==[x['iteration'] for x in full['checkpoints']];assert len(checkpoint)>=2
  targets={'peak_overflow_units':dict(peak),'sum_checkpoint_overflow_units':dict(area),'checkpoints_overused':dict(frequency)}
  for name,data in targets.items():
   original={int(n):x for n,x in full[name].items()};nodes=set(original)|set(first)|set(data)
   for n in nodes:
    expected=max(first.get(n,0),data.get(n,0)) if name=='peak_overflow_units' else first.get(n,0)+data.get(n,0) if name=='sum_checkpoint_overflow_units' else int(n in first)+data.get(n,0)
    assert original.get(n,0)==expected
  folder=out/f'{case}_{policy}';folder.mkdir();feature=dict(schema='MMC_FIRST_CHECKPOINT_OVERFLOW_FEATURES_V1',case=case,policy=policy,graph_sha256=full['graph_sha256'],cutoff_iteration=1,phase=protocol['phase'],RR_domain_size=full['RR_domain_size'],overflow_units_by_rr=first)
  future=dict(schema='MMC_STRICT_FUTURE_CHECKPOINT_TARGETS_V1',case=case,policy=policy,first_target_iteration=2,last_target_iteration=checkpoint[-1],targets=targets)
  (folder/'features.json').write_text(json.dumps(feature,separators=(',',':'))+'\n');(folder/'targets.json').write_text(json.dumps(future,separators=(',',':'))+'\n');rows.append(dict(case=case,policy=policy,first_checkpoint_end_byte=first_end,source_trace_sha256=full['source_trace_sha256'],feature_sha256=sha(folder/'features.json'),target_sha256=sha(folder/'targets.json'),future_checkpoints=len(checkpoint)-1,first_overflow_units=sum(first.values()),future_sum_overflow_units=sum(area.values()),exact_full_peak_area_frequency_decompositions_pass=True));print(case,policy,len(checkpoint)-1,flush=True)
 assert all(sha(p)==h for p,h in bindings.items());result=dict(status='all6_strict_temporal_splits_and_exact_pressure_decompositions_pass',bindings=bindings,protocol_sha256=sha(out/'protocol.json'),cases=rows,scope=protocol['scope'],new_predictor_trained=False,new_native_jobs=0,accepted_gain=False,strict_unseen_admitted=False);(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
