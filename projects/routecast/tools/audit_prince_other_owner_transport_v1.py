"""Adjacent native ownership transport diagnostic; no fitted forecast or search change."""
import json,struct,hashlib
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'experiments/prince_owned_ready_trial_v1_2026-10-20'
O=R/'experiments/prince_other_owner_transport_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 raw=p.read_bytes();assert raw[:8]==b'RCOWN001';i,count=struct.unpack_from('<QQ',raw,8);off=24;owners={}
 for _ in range(count):
  net,endpoint,n=struct.unpack_from('<QQQ',raw,off);off+=24
  owners[net]=frozenset(struct.unpack_from('<'+'Q'*n,raw,off));off+=8*n
 assert off==len(raw)
 return i,owners,Counter(node for nodes in owners.values() for node in nodes)
def main():
 assert not O.exists();proof=D/'ownership_verification_v1.json';verified=json.loads(proof.read_text());bindings={str(proof):sha(proof),str(Path(__file__)):sha(__file__)};rows=[];examples=[]
 for case_row in verified['rows']:
  case=case_row['case'];paths=sorted((D/case/'capture/owners').glob('*.bin'),key=lambda p:int(p.stem.split('_')[-1]));previous=None
  for p in paths:
   assert sha(p)==verified['bindings'][str(p)];bindings[str(p)]=sha(p);current=load(p)
   if previous:
    i,a,oa=previous;j,b,ob=current;assert j==i+1 and a.keys()==b.keys()
    changed=negative=equal_count_changed=incidences=0
    for net in a:
     for node in a[net]^b[net]:
      incidences+=1
      # Using next total demand but subtracting CURRENT ownership differs from coherent next ownership.
      mixed=ob[node]-int(node in a[net]);coherent=ob[node]-int(node in b[net]);assert abs(mixed-coherent)==1
      negative+=mixed<0;equal_count_changed+=oa[node]==ob[node];changed+=1
      if len(examples)<12 and oa[node]==ob[node]:examples.append(dict(case=case,from_iteration=i,to_iteration=j,NET=net,node=node,previous_total=oa[node],next_total=ob[node],previous_owned=node in a[net],next_owned=node in b[net],mixed_other_demand=mixed,coherent_next_other_demand=coherent))
    rows.append(dict(case=case,from_iteration=i,to_iteration=j,changed_NET_node_memberships=changed,mixed_epoch_negative_demands=negative,unchanged_total_changed_owner_memberships=equal_count_changed))
   previous=current
 assert len(rows)==218
 totals={k:sum(x[k] for x in rows) for k in ['changed_NET_node_memberships','mixed_epoch_negative_demands','unchanged_total_changed_owner_memberships']}
 assert totals['mixed_epoch_negative_demands']>0 and totals['unchanged_total_changed_owner_memberships']>0
 assert all(sha(p)==h for p,h in bindings.items());O.mkdir()
 result=dict(status='ADJACENT_OWNER_TRANSPORT_DIAGNOSIS_COMPLETE',pairs=len(rows),totals=totals,rows=rows,examples=examples,bindings=bindings,scope='Retrospective adjacent native frames, not final-target prediction quality. A next-epoch total-occupancy oracle combined with current ownership can be inconsistent. Equal total counts can hide NET-owner replacement. This does not prove inability to predict other-owner demand directly.',consumer_requirement='Predict other-owner demand directly for a declared queried NET and epoch, or supply a coherent joint ownership forecast. At active search use actual release/retained-tree state; never subtract full snapshot ownership again. Apply a replacement present term or an explicit delta, leaving native accumulated history separate. Nonconfigurable node-set aggregation and criticality weighting must follow native search semantics.',next_action='Prototype a query-level conditional demand predictor and evaluate it before native injection; retain original forecast/native/fullpaid gates.')
 (O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(pairs=len(rows),totals=totals)))
if __name__=='__main__':main()
