"""Independent raw event arithmetic and current endpoint identity joins."""
import pathlib,json,array,hashlib,sys
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_first_hint_connection_work_replay_v1_2026-10-19';rp=O/'verification.json';proof=json.loads(rp.read_text());assert proof['status']=='ALL6_CURRENT_EXPLICIT_CONNECTION_SNAPSHOTS_AND_CURRENT_CID_BINDINGS_PASS' and len(proof['rows'])==6;bindings={str(x):sha(x) for x in [rp,pathlib.Path(__file__).resolve()]};rows=[]
 for row in proof['rows']:
  case,arm=row['case'],row['arm'];trace=R/'experiments/mmc_first_hint_connection_work_v2_2026-10-19'/case/arm/'connection_trace.tsv';ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case/'demand/endpoints.json';assert proof['bindings'][str(trace)]==sha(trace) and proof['bindings'][str(ep)]==sha(ep);meta=json.loads(ep.read_text());targets={(meta['net_names'][str(q['net_id'])],q['source'],q['sink']):q['connection_id'] for q in meta['connections']};assert len(targets)==115572;names={};pins={};inverse={};sums=[array.array('Q',[0])*115572 for _ in range(4)];pending=None;sequence=iteration=completed=failed=checks=0;native=[0,0];totals=[0,0];last=[0,0];ended=False;stats_seen=False
  with trace.open() as f:
   assert next(f)=='CONNECTION_TRACE 2\n'
   for line in f:
    assert not ended;t=line.split();tag=t[0]
    if tag=='N':assert not iteration;net,ignored,count=map(int,t[1:4]);assert net not in names;names[net]=bytes.fromhex(t[4]).decode('utf8','surrogateescape');continue
    if tag=='P':assert not iteration;net,pin,rr,reached=map(int,t[1:]);assert (net,pin) not in pins;pins[net,pin]=(rr,reached);continue
    v=list(map(int,t[1:]))
    if tag=='I':
     assert pending is None and v==[iteration+1] and (iteration==0 or stats_seen)
     if iteration==0:
      for (net,pin),(rr,reached) in pins.items():
       if pin<=0:continue
       key=(names[net],pins[net,0][0],rr)
       if key in targets:assert not reached and (net,pin) not in inverse;inverse[net,pin]=targets[key]
      assert len(inverse)==len(set(inverse.values()))==115572
     iteration+=1;observed=[0,0];last=[0,0];iter_completed=0;stats_seen=False
    elif tag=='A':
     assert not stats_seen and pending is None and len(v)==8 and v[0]==sequence+1 and v[1]==iteration;assert v[4]==pins[v[2],0][0] and v[5]==pins[v[2],v[3]][0];assert (v[2],v[3]) in inverse and v[6]>=last[0] and v[7]>=last[1];sequence+=1;pending=v
    elif tag in ['C','F']:
     assert pending is not None and len(v)==6 and v[:4]==pending[:4];delta=[v[4]-pending[6],v[5]-pending[7]];assert min(delta)>=0;cid=inverse[v[2],v[3]]
     for j in range(2):sums[j][cid]+=delta[j];observed[j]+=delta[j];totals[j]+=delta[j]
     last=v[4:6];pending=None
     if tag=='C':completed+=1;iter_completed+=1;sums[2][cid]+=1
     else:failed+=1;sums[3][cid]+=1
    elif tag=='S':
     assert not stats_seen and pending is None and len(v)==7 and v[:3]==[iteration,iter_completed,iter_completed] and v[3:5]==observed
     for j in range(2):assert v[5+j]>=last[j] and v[5+j]>=observed[j];native[j]+=v[5+j]
     checks+=1;stats_seen=True
    elif tag=='END':assert stats_seen and pending is None and v==[1,sequence,completed,failed,*totals];ended=True
    else:raise AssertionError(tag)
   assert ended and checks==iteration and min(sums[2])>=1
  for j,name in enumerate(['heap_pushes','heap_pops','successful_operations','failed_attempts']):
   desc=row['vectors'][name];p=pathlib.Path(desc['path']);assert desc['values']==115572 and desc['itemsize']==8 and desc['byteorder']==sys.byteorder and sha(p)==desc['sha256'];data=array.array('Q');data.frombytes(p.read_bytes());assert data==sums[j];bindings[str(p)]=desc['sha256']
  for j,name in enumerate(['heap_pushes','heap_pops']):assert totals[j]==row['attributed_'+name] and native[j]==row['native_'+name] and native[j]-totals[j]==row['outside_sink_'+name]
  assert completed==row['successful_operations'] and failed==row['failed_attempts'] and sum(n>1 for n in sums[2])==row['distinct_repeated_CIDs'] and sum(n-1 for n in sums[2])==row['repeat_successful_operations'];mp=pathlib.Path(row['mapping']);stored=json.loads(mp.read_text());assert {(x['native_net'],x['native_pin']):x['connection_id'] for x in stored}==inverse
  for p in [trace,ep,mp]:bindings[str(p)]=sha(p)
  rows.append(dict(case=case,arm=arm,CIDs=115572,successful_operations=completed,failed_attempts=failed,native_heap_pushes=native[0],native_heap_pops=native[1],outside_sink_heap_pushes=native[0]-totals[0],outside_sink_heap_pops=native[1]-totals[1],all_current_endpoint_joins_unique=True));print('INDEPENDENT_CURRENT_CID_VECTORS_PASS',case,arm,flush=True)
 (O/'independent_verification_v1.json').open('x').write(json.dumps(dict(status='ALL6_CURRENT_CID_IDENTITY_SNAPSHOT_ARITHMETIC_AND_FULL_VECTORS_INDEPENDENTLY_VERIFIED',rows=rows,bindings=bindings,scope='Independent direct raw current NET name/pin/RR endpoint join and native-counter arithmetic, no copied historical CID mapping. Complete CID vectors, failed calls and residuals explicit. Observed work is not a causal marginal cost or a new policy benefit.'),indent=2)+'\n')
if __name__=='__main__':main()
