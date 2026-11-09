"""Independent product/odds reconstruction, separate from forward P0/P1 recurrence."""
import pathlib,json,hashlib
from fractions import Fraction
from collections import defaultdict,Counter
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_NET_prior_overflow_v1_2026-10-19';vp=O/'verification.json'
 if not vp.exists():raise SystemExit('NOT_READY: full prior statistics receipt required')
 v=json.loads(vp.read_text());assert v['status']=='ALL3_COMPLETE_NET_MARGINAL_PRIOR_STATISTICS_MATCH_EXACT_MEAN_LEDGERS'
 for p,h in v['bindings'].items():assert sha(p)==h,p
 M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';cases=[row['case'] for row in v['cases']];consumers=defaultdict(list);state={};coverage=Counter();channels=set()
 for case in cases:
  expected={int(n):Fraction(x) for n,x in json.loads((M/case/'expected_unique_NET_occupancy.json').read_text()).items()};stats=json.loads((O/case/'prior_statistics.json').read_text());maps={k:{int(n):Fraction(x) for n,x in values.items()} for k,values in stats.items()};assert set(maps)=={'expected_overflow','probability_over_capacity','jensen_gap','mean_excess'};state[case]=dict(ledger=expected,reported=maps,product={},odds=Counter(),ones=Counter())
  # The shared full domain is authenticated independently below by the bound graph.
  for index in json.loads((M/case/'NET_contribution_indices.json').read_text()):consumers[index].append(case)
 import xml.etree.ElementTree as ET
 graph=next(pathlib.Path(p) for p in v['bindings'] if p.endswith('rr_graph.xml'));stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:assert int(e.get('capacity'))==1;channels.add(int(e.get('id')))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(channels)==258720;count=0
 with (M/'NET_contributions.jsonl').open() as f:
  for line in f:
   row=json.loads(line);assert row['index']==count
   for case in consumers[count]:
    s=state[case];coverage[case]+=1
    for key,text in row['probabilities'].items():
     n=int(key)
     if n not in channels:continue
     p=Fraction(text);assert 0<p<=1
     if p==1:s['ones'][n]+=1
     else:s['product'][n]=s['product'].get(n,Fraction(1))*(1-p);s['odds'][n]+=p/(1-p)
   count+=1
   if count%10000==0:print('INDEPENDENT PRIOR CONTRIBUTIONS',count,flush=True)
 assert count==v['unique_NET_endpoint_sets'];rows=[]
 for case in cases:
  s=state[case];assert coverage[case]==55300;totals=Counter();oldtotal=Fraction(0);newtotal=Fraction(0)
  for n in channels:
   mu=s['ledger'].get(n,Fraction(0));product=s['product'].get(n,Fraction(1));ones=s['ones'][n];empty=product if ones==0 else Fraction(0);exactly_one=product*s['odds'][n] if ones==0 else product if ones==1 else Fraction(0);over=mu-1+empty;prob=1-empty-exactly_one;old=max(Fraction(0),mu-1);gap=over-old
   for key,value in [('expected_overflow',over),('probability_over_capacity',prob),('mean_excess',old),('jensen_gap',gap)]:assert s['reported'][key].get(n,Fraction(0))==value,(case,n,key)
   oldtotal+=old;newtotal+=over
   if mu<=1 and over>0:totals['mean_le1_positive_overflow']+=1
  rows.append(dict(case=case,channels_checked=len(channels),NETs=55300,mean_excess_sum=str(oldtotal),expected_overflow_sum=str(newtotal),jensen_gap_sum=str(newtotal-oldtotal),mean_at_or_below1_but_positive_expected_overflow_channels=totals['mean_le1_positive_overflow']));print('PRIOR INDEPENDENT PASS',case,flush=True)
 files=[vp,pathlib.Path(__file__).resolve()];proof=dict(status='ALL3_PRIOR_STATISTICS_INDEPENDENT_PRODUCT_ODDS_RECONSTRUCTION_PASS',bindings={str(p):sha(p) for p in files},cases=rows,verified_resource_statistics=3*258720*4,new_native_jobs=0,scope='Independent-NET Bernoulli prior identity and aggregation only; actual NET routing dependence/calibration unproven. Fixed prior expected-overflow correction is pointwise>=tested mean-excess, not evidence that a stronger surcharge helps. All prior native/final-occupancy gate failures preserved.')
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
if __name__=='__main__':main()
