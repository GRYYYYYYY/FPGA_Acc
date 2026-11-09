"""Independent raw trace arithmetic and current CID-vector check; no replay-core import."""
from pathlib import Path
import json,array,hashlib,sys
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 O=R/'experiments/mmc_preferred_NET_connection_replay_v1_2026-10-19';proof=O/'verification.json';p=json.loads(proof.read_text());rows=[];bindings={str(proof):sha(proof)}
 for row in p['rows']:
  case=row['case'];ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());targets={(meta['net_names'][str(q['net_id'])],q['source'],q['sink']):q['connection_id'] for q in meta['connections']};assert len(targets)==115572
  nets={};pins={};counts={k:[0]*115572 for k in ['heap_pushes','heap_pops','successful_operations','failed_attempts']};pending=None;seq=0;ended=False
  trace=R/f'experiments/mmc_preferred_NET_native_utility_v1_2026-10-19/{case}/connection_trace.tsv'
  with trace.open() as f:
   assert f.readline()=='CONNECTION_TRACE 2\n'
   for line in f:
    w=line.split();assert w and not ended
    if w[0]=='N':
     n=int(w[1]);assert n not in nets;nets[n]=bytes.fromhex(w[4]).decode('utf8','surrogateescape')
    elif w[0]=='P':
     key=tuple(map(int,w[1:3]));assert key not in pins;pins[key]=int(w[3])
    elif w[0]=='A':
     assert pending is None;vals=list(map(int,w[1:]));assert len(vals)==8 and vals[0]==seq+1;seq+=1;_,it,n,pin,src,sink,bp,bo=vals;assert pins[n,0]==src and pins[n,pin]==sink;cid=targets[nets[n],src,sink];pending=(vals[:4],cid,bp,bo)
    elif w[0] in ('C','F'):
     assert pending is not None;vals=list(map(int,w[1:]));identity,cid,bp,bo=pending;assert vals[:4]==identity and vals[4]>=bp and vals[5]>=bo;counts['heap_pushes'][cid]+=vals[4]-bp;counts['heap_pops'][cid]+=vals[5]-bo;counts['successful_operations' if w[0]=='C' else 'failed_attempts'][cid]+=1;pending=None
    elif w[0]=='END':
     assert pending is None;vals=list(map(int,w[1:]));assert vals==[1,seq,sum(counts['successful_operations']),sum(counts['failed_attempts']),sum(counts['heap_pushes']),sum(counts['heap_pops'])];ended=True
    else:assert w[0] in ('I','S')
  assert ended and min(counts['successful_operations'])>=1
  for name,values in counts.items():
   v=row['vectors'][name];f=Path(v['path']);assert sha(f)==v['sha256'] and v['byteorder']==sys.byteorder;a=array.array('Q');a.frombytes(f.read_bytes());assert list(a)==values;bindings[str(f)]=sha(f)
  for f in [trace,ep]:bindings[str(f)]=sha(f)
  rows.append({'case':case,'all115572_CID_vectors_equal':True,'attempts':seq});print('RAW_CID_VECTORS_PASS',case,flush=True)
 bindings[str(Path(__file__).resolve())]=sha(__file__)
 (O/'independent_raw_verification_v1.json').open('x').write(json.dumps({'status':'ALL3_INDEPENDENT_RAW_CID_VECTORS_PASS','rows':rows,'bindings':bindings},indent=2)+'\n')
if __name__=='__main__':main()
