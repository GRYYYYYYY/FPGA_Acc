"""Freeze ready/ready-1 observed query contexts without reading route labels."""
import json,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_causal_query_frontier_v1_2026-10-20';Q=E/'prince_connection_query_trial_v1_2026-10-20';L=E/'prince_ownership_ledger_trial_v2_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);start=time.perf_counter();proofp=E/'prince_query_ledger_join_v1_2026-10-20/verification.json';proof=load(proofp);bindings={str(p):sha(p) for p in [proofp,Path(__file__),E/'prince_future_arrival_exposure_v1_2026-10-20/research_decision_v1.json']}
 protocol=dict(status='CAUSAL_QUERY_INPUT_EXTRACTION_FROZEN_BEFORE_LABEL_JOIN',scope='Original9 cases,ready fixed;extract actual linker-observed CHANNEL cost contexts only at ready and ready-1. No future query row is decoded into a feature. Complete raw file hash binds provenance only.',fields='Per phase,NET,node: total cost-call multiplicity and number of saved state groups,retained-owned calls,live_other_positive calls. NET identity binds context only;not numeric learned feature.',epoch='Observed native query context is at connection entry/release-stage epoch as proven by existing independent event-ledger join. Query-time occupancy is distinct from end-phase ready occupancy;keep both meanings explicit.',future_evaluation='After freezing inputs,compare ready-only/ready-1+ready exposure support and false positives against final-owner arrivals. Do not deploy post-ready query information or turn coverage into original gate success.',limitations='All exposed development;missing width96 ready retained. Query coverage is limited to observed cost paths. No native injection,calibration model,or fullpaid claim.',bindings=dict(bindings))
 pp=D/'protocol.json';pp.write_text(json.dumps(protocol,indent=2)+'\n');bindings[str(pp)]=sha(pp);rows=[]
 for width in [96,128,160]:
  for episode in range(1,4):
   c=f'w{width:03d}/episode_{episode:02d}';rp=L/c/'capture/callback.tsv.ready.tsv';events=[int(line.split()[0]) for line in rp.open() if int(line.split()[4])];bindings[str(rp)]=sha(rp)
   if not events:rows.append(dict(case=c,status='NO_READY_EVENT'));continue
   assert len(events)==1;t=events[0];rawp=Q/c/'capture/queries.tsv';assert sha(rawp)==proof['bindings'][str(rawp)];by={t-1:{},t:{}};groups=Counter();calls=Counter();checked_future_rows=0;tick=time.perf_counter()
   with rawp.open() as f:
    for line in f:
     phase=int(line.split('\t',1)[0])
     if phase not in by:continue
     i,encoded,node,kind,occ,cap,pres,acc,base,cost,nc,active,ident,pin,sink,own,count=map(int,line.split())
     if kind not in [4,5]:continue
     assert cap==1 and active==1 and occ>=own and own in [0,1];key=(encoded-1,node);a=by[i].setdefault(key,[0,0,0,0]);a[0]+=count;a[1]+=1;a[2]+=own*count;a[3]+=(occ>own)*count;groups[i]+=1;calls[i]+=count
   out=D/c;out.mkdir(parents=True);paths={}
   for i,values in by.items():
    p=out/f'query_pairs_iteration_{i}.jsonl'
    with p.open('x') as f:
     for (net,node),(count,n,owned,other) in sorted(values.items()):f.write(json.dumps(dict(iteration=i,net=net,node=node,calls=count,state_groups=n,owned_calls=owned,live_other_positive_calls=other),separators=(',',':'))+'\n')
    paths[str(i)]=str(p);bindings[str(p)]=sha(p)
   bindings[str(rawp)]=sha(rawp);rows.append(dict(case=c,status='CAUSAL_QUERY_PAIRS_FROZEN',ready_iteration=t,iterations=[t-1,t],pairs_by_iteration={str(i):len(values) for i,values in by.items()},state_groups_by_iteration=dict(groups),calls_by_iteration=dict(calls),paths=paths,extraction_seconds=time.perf_counter()-tick));print('CAUSAL_QUERY_FROZEN',c,{i:len(values) for i,values in by.items()},flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items())
 (D/'frozen_inputs.json').write_text(json.dumps(dict(status='CAUSAL_QUERY_FRONTIERS_FROZEN_NO_LABELS_READ',rows=rows,bindings=bindings,seconds=time.perf_counter()-start),indent=2)+'\n')
if __name__=='__main__':main()
