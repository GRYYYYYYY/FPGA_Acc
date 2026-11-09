"""Freeze causal three-phase occupancy and peer local-density features, no final labels."""
import json,struct,time
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_local_history_v1_2026-10-20';SOURCE=E/'prince_input_mean_trial_v1_2026-10-20'
def read_rr(path,iteration):
 raw=path.read_bytes();assert raw[:8]==b'RCBND001';it,n=struct.unpack_from('<QQ',raw,8);rows={a:(k,o,c) for a,k,o,c,h in struct.iter_unpack('<QIiiI',raw[24:])};assert it==iteration and len(rows)==n;return rows

def main():
 D.mkdir(exist_ok=False);start=time.perf_counter();protocol=dict(status='FROZEN_BEFORE_INPUT_LABEL_JOIN',hypothesis='Short occupancy duration and observed local peer utilization can distinguish later arrivals and retention without width-specific tables.',features=dict(T='b_t+2*b_(t-1)+4*b_(t-2), each b=1 if actual same-phase native occupancy>0; no future snapshots',Q='For every frozen inclusive spatial bin of a resource: mean clipped occupied fraction of other resources in that bin. Average those bin fractions equally, retaining incidence weighting across bins; no self contribution. Quantize mean d into min(3,floor(4*d)). Exact rational arithmetic. All graph capacities1; bins need at least2 resources.'),models=dict(primary='TQ: Beta(1,1) table conditioned on(T,Q); empty cell -> T -> BP -> B -> global.',controls=['BP: last2 occupancy pattern, empty -> B -> global; must reproduce prior frozen BP metrics.','T: last3 occupancy pattern, empty -> BP -> B -> global.','BPQ: last2 pattern and Q, empty -> BP -> B -> global.']),training='Every full-domain resource once per case; fixed whole-episode leaveout across both widths,4train/2test; posterior means rounded once to binary32. No numeric IDs/width/coordinates/NET names as learned features, no threshold/hyperparameter search.',evaluation='All original9 cases retained, width96 no ready unavailable. Original capacity-normalized resource/spatial Spearman and exact fixedTopK versus previous_native/raw_min_on; ascending ID/key ties. Only primary TQ controls admission; no method union or replacement of original metrics.',cost='Three native phase snapshots and peer-density processing paid in any later fullpaid evaluation. Record extraction/evaluation/model preparation separately. Rational score adapter remains separate from physical integer ledger.',limitations='Development exposed hypothesis motivated by labels in prior diagnosis; not unseen. Read-only prediction of default-native occupancy, no native cost injection.',bindings={str(Path(__file__)):sha(__file__),str(E/'prince_temporal_residuals_v1_2026-10-20/research_decision_v1.json'):sha(E/'prince_temporal_residuals_v1_2026-10-20/research_decision_v1.json')})
 pp=D/'protocol.json';pp.write_text(json.dumps(protocol,indent=2)+'\n');bindings={str(pp):sha(pp)};rows=[]
 for width in [96,128,160]:
  for episode in range(1,4):
   case=f'w{width:03d}/episode_{episode:02d}';src=SOURCE/case/'identity';ready=src/'callback.tsv.ready.tsv';events=[int(x.split()[0]) for x in ready.read_text().splitlines() if int(x.split()[4])];bindings[str(ready)]=sha(ready)
   if not events:rows.append(dict(case=case,status='NO_READY_EVENT',features_available=False));continue
   assert len(events)==1;t=events[0];assert t>=3;tick=time.perf_counter();hist=[]
   for it in [t,t-1,t-2]:
    p=src/'boundary'/f'iteration_{it}.bin';hist.append(read_rr(p,it));bindings[str(p)]=sha(p)
   folder=E/'prince_quality_domains_v1_2026-10-20'/f'w{width:03d}';rp=folder/'resources.jsonl';bp=folder/'spatial_bins.json';resources=list(map(json.loads,rp.open()));bins=json.loads(bp.read_text());cap={tuple(b['key']):b['capacity'] for b in bins};adj=defaultdict(list);ones=Counter()
   for r in resources:
    n=r['id'];assert all(frame[n][0] in [4,5] and frame[n][1]>=0 and frame[n][2]==1 for frame in hist)
    for key in r['bins']:adj[tuple(key)].append(n);ones[tuple(key)]+=int(hist[0][n][1]>0)
   assert all(len(adj[k])==v and v>1 for k,v in cap.items());out=D/case;out.mkdir(parents=True);fp=out/'input_features.jsonl';counts=Counter()
   with fp.open('x') as f:
    for r in resources:
     n=r['id'];bits=[int(frame[n][1]>0) for frame in hist];pattern=sum(b<<i for i,b in enumerate(bits));keys=[tuple(k) for k in r['bins']];density=sum((Fraction(ones[k]-bits[0],cap[k]-1) for k in keys),Fraction())/len(keys);assert 0<=density<=1;quartile=min(3,4*density.numerator//density.denominator);counts[pattern,quartile]+=1;f.write(json.dumps(dict(id=n,T=pattern,Q=quartile,peer_density_numerator=density.numerator,peer_density_denominator=density.denominator),separators=(',',':'))+'\n')
   for p in [rp,bp,fp]:bindings[str(p)]=sha(p)
   rows.append(dict(case=case,status='FEATURES_FROZEN_NO_LABELS',iterations=[t,t-1,t-2],features=str(fp),resources=len(resources),cell_counts={f'{t},{q}':c for (t,q),c in sorted(counts.items())},extraction_seconds=time.perf_counter()-tick));print('FEATURES_FROZEN',case,dict(counts),flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'frozen_features.json').write_text(json.dumps(dict(status='LOCAL_CONTEXT_SHORT_HISTORY_FROZEN',rows=rows,bindings=bindings,extraction_seconds=time.perf_counter()-start,labels_read=False),indent=2)+'\n')
if __name__=='__main__':main()
