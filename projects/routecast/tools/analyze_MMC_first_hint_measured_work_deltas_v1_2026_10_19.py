"""Complete observed CID/NET deltas and exact symmetric arithmetic attribution."""
import pathlib,json,hashlib,array,sys
from fractions import Fraction
from collections import Counter,defaultdict
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 M=R/'experiments/mmc_first_hint_connection_work_replay_v1_2026-10-19';rp=M/'verification.json';vp=M/'independent_verification_v1.json'
 if not vp.exists():raise SystemExit('NOT_READY: current raw arithmetic/CID verification required; no output created')
 r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert v['status']=='ALL6_CURRENT_CID_IDENTITY_SNAPSHOT_ARITHMETIC_AND_FULL_VECTORS_INDEPENDENTLY_VERIFIED';assert v['bindings'][str(rp)]==sha(rp);O=R/'experiments/mmc_first_hint_measured_work_deltas_v1_2026-10-19';O.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [rp,vp,pathlib.Path(__file__).resolve()]};rows=[]
 def load(desc):
  p=pathlib.Path(desc['path']);assert sha(p)==desc['sha256']==v['bindings'][str(p)] and desc['byteorder']==sys.byteorder;values=array.array('Q');values.frombytes(p.read_bytes());assert len(values)==115572;bindings[str(p)]=sha(p);return values
 for case in ['episode_01','episode_02','episode_03']:
  ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case/'demand/endpoints.json';assert v['bindings'][str(ep)]==sha(ep);meta=json.loads(ep.read_text());qs={q['connection_id']:q for q in meta['connections']};assert set(qs)==set(range(115572));fanout=Counter(q['net_id'] for q in qs.values());assert len(fanout)==55300;arms={};summaries={}
  for arm in ['zero','forecast']:
   row=next(x for x in r['rows'] if x['case']==case and x['arm']==arm);assert row['outside_sink_heap_pushes']==row['outside_sink_heap_pops']==0;arms[arm]={name:load(desc) for name,desc in row['vectors'].items()};summaries[arm]=row
  a,b=arms['zero'],arms['forecast'];net=defaultdict(lambda:dict(zero_heap=0,hint_heap=0,zero_attempts=0,hint_attempts=0,count_term=Fraction(0),average_term=Fraction(0)));count_term=Fraction(0);average_term=Fraction(0);cidcounts=Counter();net_counts=Counter()
  for cid in range(115572):
   h0,h1=a['heap_pushes'][cid],b['heap_pushes'][cid];n0=a['successful_operations'][cid]+a['failed_attempts'][cid];n1=b['successful_operations'][cid]+b['failed_attempts'][cid];assert n0>0 and n1>0;c0,c1=Fraction(h0,n0),Fraction(h1,n1);ct=Fraction(n1-n0,2)*(c0+c1);at=Fraction(n0+n1,2)*(c1-c0);assert ct+at==h1-h0;count_term+=ct;average_term+=at;g=net[qs[cid]['net_id']];g['zero_heap']+=h0;g['hint_heap']+=h1;g['zero_attempts']+=n0;g['hint_attempts']+=n1;g['count_term']+=ct;g['average_term']+=at
   cidcounts['heap_increased' if h1>h0 else 'heap_decreased' if h1<h0 else 'heap_equal']+=1;cidcounts['attempts_increased' if n1>n0 else 'attempts_decreased' if n1<n0 else 'attempts_equal']+=1
  assert set(net)==set(fanout);delta=sum(b['heap_pushes'])-sum(a['heap_pushes']);assert count_term+average_term==delta;netrows=[]
  for nid,g in sorted(net.items()):
   dh=g['hint_heap']-g['zero_heap'];assert g['count_term']+g['average_term']==dh;net_counts['heap_increased' if dh>0 else 'heap_decreased' if dh<0 else 'heap_equal']+=1;netrows.append(dict(net_id=nid,manifest_fanout=fanout[nid],zero_heap_pushes=g['zero_heap'],hint_heap_pushes=g['hint_heap'],heap_push_delta=dh,zero_attempts=g['zero_attempts'],hint_attempts=g['hint_attempts'],attempt_delta=g['hint_attempts']-g['zero_attempts'],symmetric_count_term=str(g['count_term']),symmetric_average_work_term=str(g['average_term'])))
  assert sum(x['heap_push_delta'] for x in netrows)==delta;positive=sum(max(x['heap_push_delta'],0) for x in netrows);negative=sum(max(-x['heap_push_delta'],0) for x in netrows);assert positive-negative==delta
  fp=O/(case+'_all_NET_deltas.jsonl');fp.open('x').write(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in netrows));bindings[str(fp)]=sha(fp);bindings[str(ep)]=sha(ep)
  row=dict(case=case,CIDs=115572,NETs=55300,zero_distinct_repeated_CIDs=summaries['zero']['distinct_repeated_CIDs'],hint_distinct_repeated_CIDs=summaries['forecast']['distinct_repeated_CIDs'],zero_repeat_successful_operations=summaries['zero']['repeat_successful_operations'],hint_repeat_successful_operations=summaries['forecast']['repeat_successful_operations'],observed_heap_push_delta=delta,CID_sign_counts=dict(cidcounts),NET_sign_counts=dict(net_counts),NET_positive_delta_mass=positive,NET_negative_delta_mass=negative,exact_symmetric_count_term=str(count_term),exact_symmetric_average_work_term=str(average_term),count_term_float=float(count_term),average_work_term_float=float(average_term),top20_positive_NETs=sorted(netrows,key=lambda x:(-x['heap_push_delta'],x['net_id']))[:20]);rows.append(row);print('MEASURED_WORK_DELTA',case,'delta',delta,'count_term',float(count_term),'average_term',float(average_term),'NET_signs',dict(net_counts),flush=True)
 result=dict(status='ALL3_FULL_CID_NET_WORK_DELTAS_AND_EXACT_SYMMETRIC_ACCOUNTING_VERIFIED',cases=rows,bindings=bindings,identity='For each stable CID: H1-H0=(A1-A0)*(H0/A0+H1/A1)/2+(A0+A1)*(H1/A1-H0/A0)/2. A is measured successful+failed native calls. All calls/heaps are from validated raw snapshots.',scope='Posthoc descriptive accounting on all current fixed cases/CIDs/NETs; no fanout or footprint proxy used to allocate heap work. Count/mean terms are exact arithmetic, not causal effects; changing iterations, route trees and call mixtures remain confounded. Full signed tails retained, top20 is a display only, not a forecast selection or new acceptance gate. Distinct repeated CIDs are separate from operation counts and elapsed time.')
 (O/'review.json').open('x').write(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
