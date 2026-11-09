"""Full bound NET marginals -> unit-capacity independent-NET prior statistics.

No native target labels, new cost preload, model fitting or routing jobs.
"""
import pathlib,json,hashlib,time,xml.etree.ElementTree as ET
from collections import defaultdict,Counter
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,separators=(',',':'));f.write('\n')
def main():
 start=time.perf_counter();M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';ap=M/'independent_prediction_verification_v1.json';a=json.loads(ap.read_text());assert a['status']=='ALL3_COMPLETE_NET_ENSEMBLE_IDENTITY_XML_DAG_EXPECTATION_AND_LEDGER_AUDIT_PASS';rp=M/'receipt.json';receipt=json.loads(rp.read_text());assert a['bindings'][str(rp)]==sha(rp);spec=json.loads((M/'protocol.json').read_text());graph=next(pathlib.Path(p) for p in spec['bindings'] if p.endswith('rr_graph.xml'));assert sha(graph)==spec['bindings'][str(graph)];journal=M/'NET_contributions.jsonl';assert a['bindings'][str(journal)]==sha(journal);contract=R/'experiments/independent_NET_overflow_expectation_contract_v1_2026-10-19/verification.json';assert json.loads(contract.read_text())['fixtures']==320
 O=R/'experiments/mmc_NET_prior_overflow_v1_2026-10-19';O.mkdir();bindings={str(p):sha(p) for p in [ap,rp,M/'protocol.json',graph,journal,contract,pathlib.Path(__file__).resolve()]};write(O/'protocol.json',dict(bindings=bindings,case_order=spec['cases'],assumption='Independent NET Bernoulli inclusion perRR using admitted withinNET shared-parent inclusion marginals; sampled multiNET marginals remain empirical estimates.',recurrence='P0new=P0*(1-p); P1new=P1*(1-p)+P0*p; expected_overflow=sum(p)-1+P0; P(overused)=1-P0-P1, only capacity1 positiveCHAN',scope='Input-prior consistency diagnosis only. No native target labels, coefficient/seed/K fit or new cost/routing experiment. Not actual native probability calibration.'))
 channels=set();stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:assert int(e.get('capacity'))==1;channels.add(int(e.get('id')))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(channels)==258720;consumers=defaultdict(list);states={};coverage=Counter();rows=[]
 for case in spec['cases']:
  p=M/case/'NET_contribution_indices.json';assert a['bindings'][str(p)]==sha(p);idx=json.loads(p.read_text());assert len(idx)==len(set(idx))==55300
  for i in idx:consumers[i].append(case)
  states[case]=dict(mean=Counter(),p0={},p1={});bindings[str(p)]=sha(p)
 count=0
 with journal.open() as stream:
  for line in stream:
   row=json.loads(line);assert row['index']==count and count in consumers;prob={int(n):Fraction(v) for n,v in row['probabilities'].items() if int(n) in channels};assert all(0<p<=1 for p in prob.values())
   for case in consumers[count]:
    state=states[case];coverage[case]+=1
    for n,p in prob.items():
     old0=state['p0'].get(n,Fraction(1));old1=state['p1'].get(n,Fraction(0));state['p0'][n]=old0*(1-p);state['p1'][n]=old1*(1-p)+old0*p;state['mean'][n]+=p
   count+=1
   if count%5000==0:print('PRIOR CONTRIBUTIONS',count,flush=True)
 assert count==receipt['unique_NET_endpoint_sets'];assert all(coverage[c]==55300 for c in spec['cases'])
 for case in spec['cases']:
  lp=M/case/'expected_unique_NET_occupancy.json';assert a['bindings'][str(lp)]==sha(lp);ledger={int(n):Fraction(v) for n,v in json.loads(lp.read_text()).items()};state=states[case];mean=state['mean'];p0=state['p0'];p1=state['p1'];expected={};probability={};gap={};mean_excess={};within_mean_nonzero=0
  for n in sorted(channels):
   mu=mean.get(n,Fraction(0));assert mu==ledger.get(n,0);zero=p0.get(n,Fraction(1));one=p1.get(n,Fraction(0));assert 0<=zero<=1 and 0<=one<=1 and zero+one<=1;over=mu-1+zero;pr=1-zero-one;old=max(Fraction(0),mu-1);assert over>=old>=0 and 0<=pr<=1;assert over>=pr
   if over:expected[n]=str(over)
   if pr:probability[n]=str(pr)
   if over-old:gap[n]=str(over-old)
   if old:mean_excess[n]=str(old)
   if mu<=1 and over>0:within_mean_nonzero+=1
  d=O/case;d.mkdir();write(d/'prior_statistics.json',dict(expected_overflow=expected,probability_over_capacity=probability,jensen_gap=gap,mean_excess=mean_excess));bindings[str(lp)]=sha(lp);bindings[str(d/'prior_statistics.json')]=sha(d/'prior_statistics.json');row=dict(case=case,NETs=55300,positive_mean_excess_channels=len(mean_excess),positive_expected_overflow_channels=len(expected),positive_overcapacity_probability_channels=len(probability),positive_jensen_gap_channels=len(gap),mean_at_or_below1_but_positive_expected_overflow_channels=within_mean_nonzero,exact_mean_ledger_match=True);rows.append(row);print('PRIOR COMPLETE',row,flush=True)
 write(O/'verification.json',dict(status='ALL3_COMPLETE_NET_MARGINAL_PRIOR_STATISTICS_MATCH_EXACT_MEAN_LEDGERS',bindings=bindings,cases=rows,channel_domain=258720,unique_NET_endpoint_sets=count,component_seconds=time.perf_counter()-start,independent_reconstruction_pending=True,new_native_jobs=0,original_native_and_final_occupancy_gates_still_failed=True,scope='Derived under explicitly independent NET occupancy prior, not real routing independence. Exact algebra on admitted supplied marginals; multiNET MonteCarlo marginals are not exact true probabilities. No calibration, native usefulness, full-time or heldout claim.'))
if __name__=='__main__':main()
