"""Independent inverse-owner sets and terminal ledger oracle scoring from raw queries."""
import json,mmap,struct
from collections import defaultdict,Counter
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_ready_owner_forecast_v1_2026-10-20';L=E/'prince_ownership_ledger_trial_v2_2026-10-20';Q=E/'prince_connection_query_trial_v1_2026-10-20'
def ready_inverse(path):
 raw=path.read_bytes();offset=24;inv=defaultdict(set);n=struct.unpack_from('<Q',raw,16)[0]
 for _ in range(n):
  net,endpoint,count=struct.unpack_from('<QQQ',raw,offset);offset+=24
  for node in struct.unpack_from('<'+'Q'*count,raw,offset):inv[node].add(net)
  offset+=count*8
 assert offset==len(raw);return inv
def final_inverse(path):
 inv=defaultdict(set)
 with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  off=0;found=False
  def word():
   nonlocal off
   x=struct.unpack_from('<Q',raw,off)[0];off+=8;return x
  while off<len(raw):
   tag=word();epoch=word()
   if tag in [1,4]:word();word();n=word();off+=n*8
   elif tag==2:word();word();word();word();n=word();off+=n*8
   elif tag==3:word()
   elif tag==5:
    assert not found;found=True;n=word()
    for _ in range(n):
     net=word();count=word()
     for node in struct.unpack_from('<'+'Q'*count,raw,off):inv[node].add(net)
     off+=count*8
   else:raise AssertionError(tag)
  assert found and off==len(raw)
 return inv

def main():
 p=D/'verification.json';v=json.loads(p.read_text());bindings={str(p):sha(p),str(__file__):sha(__file__)};checked_groups=checked_calls=0;results=[]
 for row in v['rows']:
  if not row['available']:continue
  case=row['case'];op=L/case/'capture/owners'/f"owners_{row['ready_iteration']}.bin";lp=L/case/'capture/queries.tsv.ledger.bin';qp=Q/case/'capture/queries.tsv';ready=ready_inverse(op);truth=final_inverse(lp);errors=[0,0];pairs=defaultdict(Counter);forecasts={};groups=calls=0
  for line in qp.open():
   f=line.split('\t')
   if int(f[0])!=row['query_iteration'] or int(f[3]) not in [4,5]:continue
   net=int(f[1])-1;node=int(f[2]);baseline=int(f[4])-int(f[15]);count=int(f[16]);pred=len(ready[node]-{net});target=len(truth[node]-{net});assert target in [0,1];errors[0]+=abs(baseline-target)*count;errors[1]+=abs(pred-target)*count;pairs[net,node][baseline]+=1;forecasts[net,node]=(pred,target);groups+=1;calls+=count
  pair_error=[Fraction(0),Fraction(0)];varying=0
  for key,hist in pairs.items():
   pred,target=forecasts[key];mean=Fraction(sum(value*n for value,n in hist.items()),sum(hist.values()));pair_error[0]+=abs(mean-target);pair_error[1]+=abs(pred-target);varying+=len(hist)>1
  assert groups==row['groups'] and calls==row['calls'] and len(pairs)==row['unique_NET_node_pairs'];assert errors==[row['call_error_persistence'],row['call_error_ready_owner']];assert pair_error==[Fraction(*row['pair_error_persistence']),Fraction(*row['pair_error_ready_owner'])]
  results.append(dict(case=case,groups=groups,calls=calls,unique_pairs=len(pairs),pairs_with_varying_live_baseline=varying,metrics_independently_exact=True));checked_groups+=groups;checked_calls+=calls
  for path in [op,lp,qp]:bindings[str(path)]=sha(path)
 assert len(results)==6 and all(sha(p)==h for p,h in bindings.items());out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL6_QUERY_FORECAST_METRICS_INDEPENDENTLY_RECONCILED',groups=checked_groups,calls=checked_calls,rows=results,bindings=bindings,method='Raw query records; ready and terminal event-ledger inverse owner sets; group-frequency rational means. Final target independently obtained from terminal binary ledger, compared with primary original printed legal-route target.'),indent=2)+'\n');print('READY_OWNER_INDEPENDENT_PASS',checked_groups,checked_calls)
if __name__=='__main__':main()
