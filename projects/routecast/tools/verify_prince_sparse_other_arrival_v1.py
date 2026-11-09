"""Independent raw-query, inverse-owner and terminal-ledger confusion matrix audit."""
import json
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from verify_prince_ready_owner_forecast_v1 import ready_inverse,final_inverse,L,Q
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_sparse_other_arrival_v1_2026-10-20'
def cm(records):
 matrix=[[0,0],[0,0]]
 for p,y,n in records:matrix[y][p]+=n
 return dict(TP=matrix[1][1],FP=matrix[0][1],FN=matrix[1][0],TN=matrix[0][0])
def check(expected,actual):
 assert {k:expected[k] for k in actual}==actual
 n=sum(actual.values());assert expected['observations']==n
 assert expected['precision']==(actual['TP']/(actual['TP']+actual['FP']) if actual['TP']+actual['FP'] else None)
 assert expected['recall']==(actual['TP']/(actual['TP']+actual['FN']) if actual['TP']+actual['FN'] else None)
def zero_control(c):return dict(TP=0,FP=0,FN=c['TP']+c['FN'],TN=c['FP']+c['TN'],precision=None,recall=0 if c['TP']+c['FN'] else None)
def main():
 p=D/'verification.json';v=json.loads(p.read_text());bindings={str(p):sha(p),str(__file__):sha(__file__)};rows=[]
 for row in v['rows']:
  case=row['case'];readyfile=L/case/'capture/callback.tsv.ready.tsv';events=[int(x.split()[0]) for x in readyfile.read_text().splitlines() if int(x.split()[4])];assert bool(events)==row['available']
  if not row['available']:continue
  assert events==[row['ready_iteration']] and row['query_iteration']==events[0]+1;op=L/case/'capture/owners'/f'owners_{events[0]}.bin';lp=L/case/'capture/queries.tsv.ledger.bin';qp=Q/case/'capture/queries.tsv';ready=ready_inverse(op);truth=final_inverse(lp);observed=[];unique={};strata={i:[[],{}] for i in [0,1]};groups=0
  for line in qp.open():
   f=line.split('\t')
   if int(f[0])!=row['query_iteration'] or int(f[3]) not in [4,5]:continue
   own=int(f[15]);occ=int(f[4])
   if occ!=own:continue
   net=int(f[1])-1;node=int(f[2]);count=int(f[16]);pred=int(bool(ready[node]-{net}));target=int(bool(truth[node]-{net}));observed.append((pred,target,count));unique[net,node]=(pred,target);strata[own][0].append((pred,target,count));strata[own][1][net,node]=(pred,target);groups+=1
  call=cm(observed);pair=cm((p,y,1) for p,y in unique.values());check(row['metrics']['calls'],call);check(row['metrics']['unique_pairs'],pair);assert groups==row['groups'];overlap=len(strata[0][1].keys()&strata[1][1].keys());assert overlap==row['metrics']['unique_pairs_in_both_strata']
  for own,(records,pairs) in strata.items():check(row['metrics']['strata'][str(own)]['calls'],cm(records));check(row['metrics']['strata'][str(own)]['unique_pairs'],cm((p,y,1) for p,y in pairs.values()))
  rows.append(dict(case=case,groups=groups,calls=sum(call.values()),unique_pairs=len(unique),overlapping_stratum_pairs=overlap,zero_alert_calls=zero_control(call),zero_alert_unique_pairs=zero_control(pair),all_confusion_cells_and_rates_exact=True))
  for path in [readyfile,op,lp,qp]:bindings[str(path)]=sha(path)
 assert len(rows)==6 and all(sha(p)==h for p,h in bindings.items());out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL6_SPARSE_ARRIVAL_CALL_PAIR_AND_STRATIFIED_METRICS_RECONCILED',rows=rows,bindings=bindings,method='Native-ready event checked independently; raw query O=I selection; inverse-owner set differences; final target from terminal binary ledger instead of primary original printed legal route; 2x2 matrix counts. Stratum pair overlap explicit.'),indent=2)+'\n');print('SPARSE_ARRIVAL_INDEPENDENT_PASS',sum(x['calls'] for x in rows),sum(x['unique_pairs'] for x in rows))
if __name__=='__main__':main()
