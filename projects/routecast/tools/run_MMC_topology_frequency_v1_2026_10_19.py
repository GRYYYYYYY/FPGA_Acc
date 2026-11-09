"""One frozen topology-context frequency model; training folds exclude eval labels."""
import json,array,time
from pathlib import Path
from collections import Counter
from fractions import Fraction
from pre_route_endpoints import sha
from maximum_weight_NET_closure_v1 import solve,verify
R=Path(__file__).resolve().parents[1];S=10**6

def read(p):return json.loads(p.read_text())
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2)
def loadcodes(p):
 a=array.array('H');a.frombytes(p.read_bytes());assert len(a)==258720 and max(a)<13824;return a

def fit(codes,labels,training,evaluation):
 assert evaluation not in training and set(codes)==set(labels)==set(training) and len(training)==2
 counts=[0]*13824;occupied=[0]*13824
 for case in training:
  assert len(codes[case])==len(labels[case])==258720
  for c,t in zip(codes[case],labels[case]):
   assert 0<=c<13824 and t in (0,1);counts[c]+=1;occupied[c]+=t
 return dict(counts=counts,occupied=occupied,probability_int=[round(Fraction((s+1)*S,n+2)) for n,s in zip(counts,occupied)],scale=S,training_cases=training,evaluation_case=evaluation)

def main():
 ctx=R/'experiments/mmc_topology_context_v1_2026-10-19';proof=read(ctx/'receipt.json');assert not proof['target_final_labels_read'];independent=read(ctx/'independent_verification_v1.json');assert independent['status']=='ALL3_ORIGINAL_XML_POSITIVE_AND_ZERO_FLAGS_AND_CODES_INDEPENDENTLY_VERIFIED' and independent['bindings'][str(ctx/'receipt.json')]==sha(ctx/'receipt.json');out=R/'experiments/mmc_topology_frequency_development_v1_2026-10-19';out.mkdir(exist_ok=False);cp=R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32';nodes=array.array('I');nodes.frombytes(cp.read_bytes());channel=set(nodes);master=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=read(master);items={x['case']:x for x in plan['cases']};cases=list(items);bindings={str(p):sha(p) for p in [ctx/'protocol.json',ctx/'receipt.json',cp,master,Path(__file__).resolve(),R/'tools/maximum_weight_NET_closure_v1.py']};rows=[]
 for case in cases:
  begin=time.perf_counter();training=[c for c in cases if c!=case];codes={};labels={}
  for c in training:
   p=ctx/(c+'.u16');assert proof['bindings'][str(p)]==sha(p);codes[c]=loadcodes(p);tp=Path(items[c]['native_label']);assert plan['bindings'][str(tp)]==sha(tp);truth={int(n):v for n,v in read(tp)['node_occupancy'].items()};labels[c]=[truth.get(n,0) for n in nodes];bindings.update({str(p):sha(p),str(tp):sha(tp)})
  m=fit(codes,labels,training,case);del codes,labels,truth
  directory=out/case;directory.mkdir();write(directory/'model.json',m)
  # Frozen model exists before evaluation context; no eval label used by fit.
  p=ctx/(case+'.u16');assert proof['bindings'][str(p)]==sha(p);test=loadcodes(p);prob=[m['probability_int'][c] for c in test];gp=R/f'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/{case}/graph.json';bp=gp.with_name('banks.jsonl');g=read(gp);banks={x['net_id']:(set(x['A']),set(x['B'])) for x in map(json.loads,bp.open())};assert set(banks)==set(g['nodes']) and len(banks)==55300
  A=Counter(n for a,b in banks.values() for n in a);B=Counter(n for a,b in banks.values() for n in b);safe={n for n in channel if A[n]<=1 and B[n]<=1};coeff={n:S-2*p for n,p in zip(nodes,prob) if n in safe};weights={net:sum(coeff[n] for n in (a-b)&safe)-sum(coeff[n] for n in (b-a)&safe) for net,(a,b) in banks.items()};encoded={n:55301*w-1 for n,w in weights.items()};groups=g['components'];cw={i:sum(encoded[n] for n in group) for i,group in enumerate(groups)};edges=list(map(tuple,g['condensation_edges']));cert=solve(cw,edges);verify(cw,edges,cert);chosen={n for i in cert['selected'] for n in groups[i]};assert all(e['source'] not in chosen or e['target'] in chosen for e in g['edges']);ledger=Counter(n for net,(a,b) in banks.items() for n in (b if net in chosen else a));assert all(ledger[n]<=1 for n in safe|set(g['eligible_resources']));gain=sum(weights[n] for n in chosen);assert cert['objective']==55301*gain-len(chosen)
  with (directory/'choices.jsonl').open('x') as f:
   for n in sorted(banks):f.write(json.dumps(dict(net_id=n,expected_gain_scaled=weights[n],encoded_weight=encoded[n],pick='B' if n in chosen else 'A'))+'\n')
  (directory/'probabilities.u32').write_bytes(array.array('I',prob).tobytes());write(directory/'flow_cut_certificate.json',cert);write(directory/'ledger.json',dict(ledger));rows.append(dict(case=case,training_cases=training,training_resources=sum(m['counts']),B_NETs=len(chosen),changed_NETs=sum(banks[n][0]!=banks[n][1] for n in chosen),safe_CHANNELs=len(safe),expected_gain_scaled=gain,component_seconds=time.perf_counter()-begin,heldout_labels_used_for_model=False,eligible_for_legal_route_commit=False))
  for p in [p,gp,bp,*directory.iterdir()]:bindings[str(p)]=sha(p)
  print('TOPOLOGY_FREQUENCY_FIXED_FOLD',case,rows[-1]['changed_NETs'],flush=True)
 write(out/'receipt.json',dict(status='ALL3_FIXED_TOPOLOGY_CONTEXT_FOLDS_AND_CLOSED_CHOICES_PRODUCED',rows=rows,bindings=bindings,independent_verification_pending=True,quality_evaluation_executed=False,scope='Exposed development layouts only; upstream prefix, A/B banks and audits paid. No native utility or full flow gain.'))
if __name__=='__main__':main()
