"""Raw query -> independent update-history epoch + retained ownership + scalar identity."""
import json,mmap,struct,bisect
from collections import defaultdict,Counter
from pathlib import Path
from pre_route_endpoints import sha
from conditional_present_capacity_one_v1 import present_bits,f32,bits
R=Path(__file__).resolve().parents[1];L=R/'experiments/prince_ownership_ledger_trial_v2_2026-10-20';Q=R/'experiments/prince_connection_query_trial_v1_2026-10-20';D=R/'experiments/prince_query_ledger_join_v1_2026-10-20'
def number(x):return struct.unpack('<f',struct.pack('<I',x))[0]
def history(path):
 owners=defaultdict(set);counts=Counter();times=defaultdict(lambda:[0]);values=defaultdict(lambda:[0]);entries={};epoch=0;iteration=1
 with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  off=0
  def word():
   nonlocal off
   x=struct.unpack_from('<Q',raw,off)[0];off+=8;return x
  def nodes():
   nonlocal off
   n=word();group=struct.unpack_from('<'+'Q'*n,raw,off);off+=n*8;assert len(set(group))==n;return group
  while off<len(raw):
   tag=word();e=word()
   if tag in [1,4]:
    assert e==epoch+1;epoch=e;net=word();sign=word();group=nodes();own=owners[net]
    for node in group:
     if sign:assert node not in own;own.add(node);counts[node]+=1
     else:assert node in own;own.remove(node);counts[node]-=1
     assert counts[node]>=0;times[node].append(e);values[node].append(counts[node])
   elif tag==2:
    assert e==epoch;ident=word();net=word();pin=word();sink=word();actual=nodes();assert set(actual)==owners[net];assert ident not in entries;entries[ident]=(e,iteration,net,pin,sink,frozenset(owners[net]))
   elif tag==3:assert e==epoch and word()==iteration;iteration+=1
   elif tag==5:
    assert e==epoch;n=word()
    for _ in range(n):net=word();assert set(nodes())==owners[net]
    assert off==len(raw)
   else:raise AssertionError(tag)
 return entries,times,values

def main():
 assert not D.exists();D.mkdir();lp=L/'ledger_verification_v1.json';qp=Q/'connection_query_verification_v1.json';ledger=json.loads(lp.read_text());prior=json.loads(qp.read_text());bindings={str(p):sha(p) for p in [lp,qp,Path(__file__),R/'tools/conditional_present_capacity_one_v1.py',L/'conditional_present_consumer_design_v1.json']};(D/'protocol.json').write_text(json.dumps(dict(scope='Cross-run identity join of already-recorded actual cost calls to separately observed update-event ledger, all9 fixed cases. No new forecast, no price injection. Capacity-one scalar identity F=O-I checked against actual native returned cost words.',bindings=dict(bindings)),indent=2)+'\n');rows=[]
 for case in sorted(x['case'] for x in ledger['rows']):
  event=L/case/'capture/queries.tsv.ledger.bin';rawp=Q/case/'capture/queries.tsv';assert sha(event)==ledger['bindings'][str(event)] and sha(rawp)==prior['bindings'][str(rawp)];entries,times,values=history(event);calls=channel_calls=groups=channel_groups=owned_calls=0;seen=set();present_cache={};scalar_cache=set()
  for line in rawp.open():
   i,encoded,node,kind,occ,cap,pres,acc,base,cost,nc,active,ident,pin,sink,owns,count=map(int,line.split());groups+=1;calls+=count;e,iteration,net,target_pin,target,retained=entries[ident];assert active==1 and (i,encoded-1,pin,sink)==(iteration,net,target_pin,target);seen.add(ident)
   if kind not in [4,5]:continue
   assert cap==1 and owns==int(node in retained);index=bisect.bisect_right(times[node],e)-1;assert values[node][index]==occ,(case,i,ident,node,occ,values[node][index]);assert occ>=owns;channel_calls+=count;channel_groups+=1;owned_calls+=count*owns
   key=(occ,owns,pres)
   if key not in present_cache:present_cache[key]=present_bits(1,owns,float(occ-owns),pres)
   scalar=(occ,owns,pres,acc,base,cost)
   if scalar not in scalar_cache:
    assert nc==0;expected=f32(f32(number(base)*number(acc))*number(present_cache[key]));assert bits(expected)==cost;scalar_cache.add(scalar)
  assert seen<=entries.keys();old=next(x for x in prior['rows'] if x['case']==case);assert calls==old['cost_calls'] and groups==old['unique_query_state_groups'];row=dict(case=case,raw_query_state_groups=groups,native_cost_calls=calls,CHANNEL_groups_with_independent_epoch_join=channel_groups,CHANNEL_calls_with_independent_epoch_join=channel_calls,retained_owned_CHANNEL_calls=owned_calls,unique_present_identity_inputs=len(present_cache),unique_native_cost_identity_inputs=len(scalar_cache),connections_with_query_joins=len(seen),entry_contexts=len(entries));rows.append(row);bindings[str(event)]=sha(event);bindings[str(rawp)]=sha(rawp);print('QUERY_LEDGER_IDENTITY_CASE_PASS',case,channel_calls,len(scalar_cache),flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL9_QUERY_EPOCH_OWNERSHIP_AND_CAPACITY_ONE_IDENTITY_PASS',rows=rows,bindings=bindings,limitations=['Cross-run deterministic observation join, not same-process replay or coverage of every inlined cost path.','Independent ledger join applies CHANNELs; nonCHANNEL query contexts checked without CHANNEL occupancy reconstruction.','Capacity-one identity scalar reproduces current native costs; no future forecast quality, native implementation or whole-search replacement parity claimed.']),indent=2)+'\n')
if __name__=='__main__':main()
