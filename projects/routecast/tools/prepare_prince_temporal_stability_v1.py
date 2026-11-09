"""Freeze label-free consecutive phase ownership features before fitting."""
import json,struct,hashlib
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_temporal_stability_v1_2026-10-20';S=E/'prince_input_mean_trial_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def owners(path):
 raw=path.read_bytes();assert raw[:8]==b'RCOWN001';it,count=struct.unpack_from('<QQ',raw,8);off=24;inverse=defaultdict(set);seen=set()
 for _ in range(count):
  net,endpoint,n=struct.unpack_from('<QQQ',raw,off);off+=24;assert net not in seen;seen.add(net);nodes=struct.unpack_from('<'+'Q'*n,raw,off);off+=8*n;assert len(set(nodes))==n
  for node in nodes:inverse[node].add(net)
 assert off==len(raw);return it,inverse

def main():
 D.mkdir(exist_ok=False)
 protocol=dict(status='FROZEN_BEFORE_FEATURE_LABEL_JOIN',hypothesis='Recent occupied persistence and exact owner-set retention distinguish stable routes from transient congestion footprint.',target='Full-domain final default-native uniqueNET occupancy, unit-capacity CHANNELs.',features=['B: current ready occupancy>0','P: immediately previous same-phase occupancy>0','S: both occupied and exact native NET owner sets unchanged across those phases. No numeric NET identity enters model.'],model='Fixed Beta(1,1) eight-cell B/P/S table, binary32 means. Empty cell backs off to B/P then B then global. Controls same-fold B-only and B/P four-cell posterior; no tuning or per-case selection.',split='Entire episode held out across both widths; four train and two test per fold; development exposed.',evaluation='Original9 cases,full resource/spatial universes,original two-control four-metric gates and ascending ties. Width96 no ready remains unavailable. Same rational expected-count adapter; no physical ledger changes or native injection.',costs='Requires two complete phase owner snapshots; capture and model costs must be accounted before fullpaid claim.',bindings={str(Path(__file__)):sha(__file__),str(E/'prince_history_rank_split_v1_2026-10-20/research_decision_v1.json'):sha(E/'prince_history_rank_split_v1_2026-10-20/research_decision_v1.json')})
 (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');bindings={str(D/'protocol.json'):sha(D/'protocol.json')};rows=[]
 for w in [96,128,160]:
  for ep in range(1,4):
   case=f'w{w:03d}/episode_{ep:02d}';src=S/case/'identity';rp=src/'callback.tsv.ready.tsv';events=[int(x.split()[0]) for x in rp.read_text().splitlines() if int(x.split()[4])];bindings[str(rp)]=sha(rp)
   if not events:rows.append(dict(case=case,status='NO_READY_EVENT',features_available=False));continue
   assert len(events)==1;it=events[0];assert it>=2;inv=[];rrs=[]
   for t in [it-1,it]:
    op=src/'owners'/f'owners_{t}.bin';t0,own=owners(op);assert t0==t;bp=src/'boundary'/f'iteration_{t}.bin';raw=bp.read_bytes();assert raw[:8]==b'RCBND001';ti,nrr=struct.unpack_from('<QQ',raw,8);assert ti==t;rr={n:(kind,occ,cap) for n,kind,occ,cap,acc in struct.iter_unpack('<QIiiI',raw[24:])};assert len(rr)==nrr
    for n,(kind,occ,cap) in rr.items():
     if kind in [4,5]:assert occ==len(own.get(n,set()))
    inv.append(own);rrs.append(rr)
    for p in [op,bp]:bindings[str(p)]=sha(p)
   domainp=E/'prince_quality_domains_v1_2026-10-20'/f'w{w:03d}'/'resources.jsonl';resources=list(map(json.loads,domainp.open()));bindings[str(domainp)]=sha(domainp);folder=D/case;folder.mkdir(parents=True);fp=folder/'input_features.jsonl';cells=Counter();changes=0
   with fp.open('x') as f:
    for r in resources:
     n=r['id'];prev=inv[0].get(n,set());cur=inv[1].get(n,set());b=int(bool(cur));p=int(bool(prev));s=int(bool(cur) and cur==prev);assert all(rr[n][2]==1 for rr in rrs);assert rrs[1][n][1]==len(cur);cells[b,p,s]+=1;changes+=prev!=cur
     f.write(json.dumps(dict(id=n,B=b,P=p,S=s,previous_count=len(prev),current_count=len(cur)),separators=(',',':'))+'\n')
   bindings[str(fp)]=sha(fp);rows.append(dict(case=case,status='FEATURES_FROZEN_NO_LABELS',iterations=[it-1,it],resources=len(resources),changed_owner_sets=changes,cells={','.join(map(str,k)):v for k,v in sorted(cells.items())},features=str(fp)));print(case,changes,dict(cells),flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items())
 (D/'frozen_features.json').write_text(json.dumps(dict(status='TEMPORAL_INPUTS_FROZEN_BEFORE_LABEL_JOIN',rows=rows,bindings=bindings,scope='No final labels read by this producer; same-phase RR occupancy independently checked against owner inverse for both snapshots. Not an accuracy/native/fullpaid claim.'),indent=2)+'\n')
if __name__=='__main__':main()
