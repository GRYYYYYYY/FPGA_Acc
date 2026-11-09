"""Independent histogram, integer rounding, resource-scatter and flow/cut checks."""
import json,array
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from maximum_weight_NET_closure_v1 import verify
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def ar(p,t):
 x=array.array(t);x.frombytes(p.read_bytes());return x

def main():
 root=R/'experiments/mmc_owner_frequency_development_v1_2026-10-19';rp=root/'receipt.json';receipt=read(rp);assert receipt['status']=='ALL3_FIXED_OWNER_CONTEXT_FOLDS_AND_CLOSED_CHOICES_PRODUCED';assert all(sha(p)==h for p,h in receipt['bindings'].items())
 ctx=R/'experiments/mmc_resource_owner_context_v1_2026-10-19';ids=ar(R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32','I');channels=set(ids);plan=read(R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json');items={x['case']:x for x in plan['cases']};rows=[]
 for row in receipt['rows']:
  case=row['case'];directory=root/case;m=read(directory/'model.json');train=sorted(set(items)-{case});assert m['training_cases']==train and m['evaluation_case']==case and row['training_resources']==517440;hist=Counter()
  for c in train:
   p=Path(items[c]['native_label']);assert sha(p)==plan['bindings'][str(p)];truth={int(n):v for n,v in read(p)['node_occupancy'].items()}
   for n,code in zip(ids,ar(ctx/(c+'.u16'),'H')):hist[code,truth.get(n,0)]+=1
  N=[hist[i,0]+hist[i,1] for i in range(3456)];S=[hist[i,1] for i in range(3456)];assert N==m['counts'] and S==m['occupied'] and sum(N)==517440
  table=[]
  for n,s in zip(N,S):
   q,r=divmod((s+1)*10**6,n+2);table.append(q+int(2*r>n+2 or (2*r==n+2 and q%2==1)))
  assert table==m['probability_int'];prob=ar(directory/'probabilities.u32','I');assert list(prob)==[table[c] for c in ar(ctx/(case+'.u16'),'H')]
  bp=R/f'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/{case}/banks.jsonl';banks={b['net_id']:b for b in map(json.loads,bp.open())};g=read(bp.with_name('graph.json'));owners=[defaultdict(set),defaultdict(set)]
  for net,b in banks.items():
   for i,key in enumerate(['A','B']):
    for n in b[key]:
     if n in channels:owners[i][n].add(net)
  safe={n for n in channels if len(owners[0][n])<=1 and len(owners[1][n])<=1};weights={n:0 for n in banks}
  for n,p in zip(ids,prob):
   if n not in safe:continue
   for net in owners[0][n]:weights[net]+=10**6-2*p
   for net in owners[1][n]:weights[net]-=10**6-2*p
  choices={x['net_id']:x for x in map(json.loads,(directory/'choices.jsonl').open())};assert set(choices)==set(banks);chosen=set()
  for net,w in weights.items():
   c=choices[net];assert c['expected_gain_scaled']==w and c['encoded_weight']==55301*w-1 and c['pick'] in ('A','B')
   if c['pick']=='B':chosen.add(net)
  groups=g['components'];cw={i:sum(55301*weights[n]-1 for n in group) for i,group in enumerate(groups)};cert=read(directory/'flow_cut_certificate.json');objective=verify(cw,list(map(tuple,g['condensation_edges'])),cert);assert {n for i in cert['selected'] for n in groups[i]}==chosen;assert all(e['source'] not in chosen or e['target'] in chosen for e in g['edges']);gain=sum(weights[n] for n in chosen);assert objective==55301*gain-len(chosen) and gain==row['expected_gain_scaled']
  ledger=Counter()
  for net,b in banks.items():ledger.update(b['B'] if net in chosen else b['A'])
  assert dict(ledger)=={int(n):v for n,v in read(directory/'ledger.json').items()};assert all(ledger[n]<=1 for n in safe|set(g['eligible_resources']));assert len(chosen)==row['B_NETs'];assert sum(banks[n]['A']!=banks[n]['B'] for n in chosen)==row['changed_NETs'];rows.append(dict(case=case,training_resources=sum(N),safe_CHANNELs=len(safe),changed_NETs=row['changed_NETs']));print('OWNER_FREQUENCY_INDEPENDENT_PASS',case,flush=True)
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_OWNER_FREQUENCY_HISTOGRAMS_INTEGER_ROUNDING_SCATTER_FLOWCUT_AND_LEDGER_PASS',rows=rows,bindings={str(p):sha(p) for p in [rp,Path(__file__).resolve()]},scope='Numerical/train-fold and candidate-membership checks; upstream source and original physical path proofs inherited. No quality claim.'),f,indent=2)
if __name__=='__main__':main()
