"""Independent raw snapshot summation, complete CID vectors and native totals."""
import array,hashlib,json,sys
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 root=R/'experiments/mmc_native_connection_work_replay_v1_2026-10-18';receipt=root/'verification.json';proof=json.loads(receipt.read_text());assert len(proof['rows'])==6
 query=R/'experiments/native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';inverse={}
 for line in query.read_text().splitlines():
  t=line.split()
  if t[0]=='Q':cid,net,pin=map(int,t[1:4]);assert (net,pin) not in inverse;inverse[net,pin]=cid
 assert len(inverse)==115572
 bindings={str(receipt):digest(receipt),str(query):digest(query),str(Path(__file__)):digest(__file__)};rows=[]
 for row in proof['rows']:
  trace=R/'experiments/mmc_native_connection_work_cascade_trace_v1_2026-10-18'/row['case']/row['arm']/'connection_trace.tsv';assert digest(trace)==proof['bindings'][str(trace)];bindings[str(trace)]=proof['bindings'][str(trace)]
  sums=[array.array('Q',[0])*115572,array.array('Q',[0])*115572];pending=None;sequence=0;completed=failed=0;totals=[0,0];native=[0,0];iteration=0;observed=[0,0];last=[0,0];checks=0
  with trace.open() as f:
   assert next(f)=='CONNECTION_TRACE 2\n';ended=False
   for line in f:
    assert not ended;t=line.split();tag=t[0]
    if tag in ('N','P'):continue
    v=list(map(int,t[1:]))
    if tag=='I':
     assert pending is None and v==[iteration+1];iteration+=1;observed=[0,0];last=[0,0];iter_completed=0
    elif tag=='A':
     assert pending is None and len(v)==8 and v[0]==sequence+1 and v[1]==iteration;sequence+=1
     assert v[6]>=last[0] and v[7]>=last[1];pending=v
    elif tag in ('C','F'):
     assert pending is not None and v[:4]==pending[:4];delta=[v[4]-pending[6],v[5]-pending[7]];assert min(delta)>=0
     key=(v[2],v[3]);assert key in inverse or delta==[0,0]
     for j in range(2):
      if key in inverse:sums[j][inverse[key]]+=delta[j]
      observed[j]+=delta[j];totals[j]+=delta[j]
     last=v[4:6];pending=None
     if tag=='C':completed+=1;iter_completed+=1
     else:failed+=1
    elif tag=='S':
     assert pending is None and v[:3]==[iteration,iter_completed,iter_completed] and v[3:5]==observed
     assert all(v[5+j]>=last[j] and v[5+j]>=observed[j] for j in range(2))
     for j in range(2):native[j]+=v[5+j]
     checks+=1
    elif tag=='END':assert v==[1,sequence,completed,failed,*totals];ended=True
    else:raise AssertionError(tag)
   assert ended and pending is None and checks==iteration
  for j,name in enumerate(('heap_pushes','heap_pops')):
   desc=row['vectors'][name];p=Path(desc['path']);assert desc['byteorder']==sys.byteorder and desc['itemsize']==8 and digest(p)==desc['sha256'];a=array.array('Q');a.frombytes(p.read_bytes());assert a==sums[j] and len(a)==115572;bindings[str(p)]=desc['sha256'];assert totals[j]==row['attributed_'+name] and native[j]==row['native_'+name] and native[j]-totals[j]==row['outside_sink_'+name]
  rows.append(dict(case=row['case'],arm=row['arm'],CIDs=115572,attempts=sequence,native_heap_pushes=native[0],native_heap_pops=native[1],outside_heap_pushes=native[0]-totals[0],outside_heap_pops=native[1]-totals[1],iterations=checks));print('INDEPENDENT HEAP VECTORS PASS',row['case'],row['arm'],flush=True)
 target=root/'independent_verification_v1.json'
 with target.open('x') as f:json.dump(dict(status='all693432CID_heap_push_pop_vectors_independently_verified',bindings=bindings,rows=rows,scope='Independent raw before/after snapshot arithmetic, nonoverlapping monotone counters, complete CID zeros and native residual conservation. Prior certified identity transfer remains prerequisite; no elapsed-time or causal gain claim.'),f,indent=2)
if __name__=='__main__':main()
