"""Posthoc necessary occupancy-error floor for fixed clean NET unions; no predictor."""
from pathlib import Path
import json, hashlib, array, sys
from collections import defaultdict, Counter
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'experiments/mmc_frozen_clean_error_floor_v1_2026-10-18';out.mkdir()
 bindings={str(Path(__file__).resolve()):sha(__file__)}
 def load(p):
  p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
 idx=load(R/'experiments/real_joint_full_score_v2_2026-10-18/graph_index.json');meta=idx['arrays']['edge_destination'];assert sys.byteorder==idx['byteorder']=='little';assert sha(meta['path'])==meta['sha256'];bindings[meta['path']]=meta['sha256'];dest=array.array('I');dest.frombytes(Path(meta['path']).read_bytes());assert len(dest)==meta['values']
 rows=[]
 for case in ['case_01','case_02','case_03']:
  warm=R/f'experiments/mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained';w=load(warm/'verification.json');assert all(sha(k)==h for k,h in w['bindings'].items());bindings.update(w['bindings']);dirty=set(w['dirty_nets']);frame=load(warm/'initial.json');assert frame['graph_sha256']==idx['graph_sha256'];unions=defaultdict(set)
  for rec in frame['records']:
   ns=unions[rec['net_id']];ns.add(rec['source']);ns.update(dest[e] for e in rec['answer']['physical_edge_ids'])
  assert dict(Counter(n for ns in unions.values() for n in ns))=={int(k):v for k,v in frame['ledger'].items()}
  clean=Counter(n for net,ns in unions.items() if net not in dirty for n in ns)
  quality=R/f'experiments/mmc_atomic_pair_quality_v1_2026-10-18/{case}';comparison=load(quality/'comparison.json');vectorpath=quality/'vectors.json';assert comparison['bindings'][str(vectorpath)]==sha(vectorpath);vectors=load(vectorpath)['channels'];lower=errors=excess_nodes=0;by_method=Counter();witnesses=[]
  for v in vectors:
   n=v['node'];truth=v['labels']['cold'];c=clean[n];floor=max(c-truth,truth-c-len(dirty),0);lower+=floor;excess_nodes+=floor>0
   for method,value in v['predictions'].items():by_method[method]+=abs(value-truth)
   if floor and len(witnesses)<16:witnesses.append(dict(node=n,clean_NETs=c,target=truth,unavoidable_absolute_error=floor))
  assert lower<=by_method['native_retained_on'] and lower<=by_method['atomic_coowner_pair_v1']
  rows.append(dict(case=case,dirty_NETs=len(dirty),clean_NETs=len(unions)-len(dirty),channel_count=len(vectors),unavoidable_channel_L1_units=lower,unavoidable_error_channels=excess_nodes,observed_channel_L1_units=dict(by_method),fraction_of_original_candidate_L1_lower_bound=lower/by_method['native_retained_on'],fraction_of_atomic_pair_L1_lower_bound=lower/by_method['atomic_coowner_pair_v1'],witnesses=witnesses));print(case,lower,excess_nodes,flush=True)
 assert all(sha(k)==h for k,h in bindings.items())
 result=dict(status='posthoc_fixed_clean_occupancy_error_floor_computed',bindings=bindings,cases=rows,derivation='At each channel, any candidate changing only D dirty NETs has integer occupancy in [clean, clean+D]. Distance of target occupancy from that interval is a necessary L1 error floor. Sum over the full frozen positive-capacity channel universe. Relaxing all path, budget and topology restrictions only weakens this floor.',scope='Development-label diagnostic, not an estimator, attainable path solution, ranking-metric bound, causal attribution or unseen result. Arbitrary all-NET policies are outside the fixed-clean premise.',accepted_gain=False)
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
