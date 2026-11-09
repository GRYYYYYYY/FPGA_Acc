"""Independent NET member grouping and exact rational count/average decomposition."""
import pathlib,json,array,hashlib
from collections import defaultdict,Counter
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_first_hint_measured_work_deltas_v1_2026-10-19';rp=O/'review.json';r=json.loads(rp.read_text());M=R/'experiments/mmc_first_hint_connection_work_replay_v1_2026-10-19';v=json.loads((M/'verification.json').read_text());bindings={str(p):sha(p) for p in [rp,M/'verification.json',pathlib.Path(__file__).resolve()]};rows=[]
 for summary in r['cases']:
  case=summary['case'];ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case/'demand/endpoints.json';assert r['bindings'][str(ep)]==sha(ep);members=defaultdict(list)
  for q in json.loads(ep.read_text())['connections']:members[q['net_id']].append(q['connection_id'])
  vectors={}
  for arm in ['zero','forecast']:
   row=next(x for x in v['rows'] if x['case']==case and x['arm']==arm);vectors[arm]={}
   for name,desc in row['vectors'].items():
    p=pathlib.Path(desc['path']);assert r['bindings'][str(p)]==sha(p)==desc['sha256'];a=array.array('Q');a.frombytes(p.read_bytes());assert len(a)==115572;vectors[arm][name]=a
  a,b=vectors['zero'],vectors['forecast'];fp=O/(case+'_all_NET_deltas.jsonl');assert r['bindings'][str(fp)]==sha(fp);seen=set();count_total=Fraction(0);average_total=Fraction(0);positive=negative=0;counts=Counter()
  with fp.open() as f:
   for line in f:
    row=json.loads(line);net=row['net_id'];assert net in members and net not in seen;seen.add(net);cids=members[net];assert row['manifest_fanout']==len(cids);ct=Fraction(0)
    h0=sum(a['heap_pushes'][c] for c in cids);h1=sum(b['heap_pushes'][c] for c in cids);n0=sum(a['successful_operations'][c]+a['failed_attempts'][c] for c in cids);n1=sum(b['successful_operations'][c]+b['failed_attempts'][c] for c in cids)
    assert [h0,h1,n0,n1,h1-h0,n1-n0]==[row[k] for k in ['zero_heap_pushes','hint_heap_pushes','zero_attempts','hint_attempts','heap_push_delta','attempt_delta']]
    for c in cids:
     x=a['successful_operations'][c]+a['failed_attempts'][c];y=b['successful_operations'][c]+b['failed_attempts'][c];ct+=Fraction((y-x)*(a['heap_pushes'][c]*y+b['heap_pushes'][c]*x),2*x*y)
    at=Fraction(h1-h0)-ct;assert ct==Fraction(row['symmetric_count_term']) and at==Fraction(row['symmetric_average_work_term']);count_total+=ct;average_total+=at;positive+=max(h1-h0,0);negative+=max(h0-h1,0);counts['heap_increased' if h1>h0 else 'heap_decreased' if h1<h0 else 'heap_equal']+=1
  assert seen==set(members) and len(seen)==55300;assert positive==summary['NET_positive_delta_mass'] and negative==summary['NET_negative_delta_mass'];assert dict(counts)==summary['NET_sign_counts'] and positive-negative==summary['observed_heap_push_delta'];assert count_total==Fraction(summary['exact_symmetric_count_term']) and average_total==Fraction(summary['exact_symmetric_average_work_term']);rows.append(dict(case=case,all_NETs_checked=55300,all_CIDs_grouped=sum(map(len,members.values())),heap_delta=positive-negative,exact_count_term=str(count_total),exact_average_term=str(average_total)));bindings[str(fp)]=sha(fp);bindings[str(ep)]=sha(ep);print('INDEPENDENT_NET_WORK_DELTAS_PASS',case,flush=True)
 (O/'independent_verification_v1.json').open('x').write(json.dumps(dict(status='ALL3_COMPLETE_NET_SUMS_AND_SYMMETRIC_ARITHMETIC_INDEPENDENTLY_VERIFIED',cases=rows,bindings=bindings,scope='Independent complete member grouping and rational formula verification only. Posthoc count/average-work terms do not establish causal effects or new routing policy benefit.'),indent=2)+'\n')
if __name__=='__main__':main()
