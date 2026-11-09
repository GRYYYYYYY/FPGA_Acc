"""Independent bit memberships, pointwise affine identities and bucket-plan audit."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from itertools import combinations
from math import prod
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_reduced_L1_factor_profile_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=D/'verification.json';v=read(source);assert all(sha(p)==h for p,h in v['bindings'].items());graphs={};rows=[];identities=0;nodes_verified=0
 for row in v['rows']:
  ep=read(row['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.get('sink_node')) for _,e in ET.iterparse(g) if e.tag=='edge']
  dest=graphs[g];channels={json.loads(x)['id'] for x in Path(row['resources']).read_text().splitlines()};out=Path(row['output']);initial=defaultdict(list);pools=defaultdict(list)
  def add(net,rs):
   mask=0
   for q in rs:
    for e in q['answer']['physical_edge_ids']:
     n=dest[e]
     if n in channels:mask|=1<<n
   if mask not in pools[net]:pools[net].append(mask)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for net,rs in sorted(initial.items()):add(net,rs)
  for rnd in read(out/'receipt.json')['rounds']:
   for event in rnd['events']:
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:add(event['net_id'],rs)
  fixed=Counter();patterns=defaultdict(dict);cards={n:len(cs) for n,cs in pools.items()}
  for net,choices in pools.items():
   common=-1;union=0
   for m in choices:common&=m;union|=m
   mask=union
   while mask:
    bit=mask&-mask;n=bit.bit_length()-1
    if common&bit:fixed[n]+=1
    else:patterns[n][net]=[int(bool(choice&bit)) for choice in choices]
    mask-=bit
  p=read(row['payload']);f=p['factors'];assert cards=={int(n):d for n,d in f['cardinalities'].items()};truth={int(n):c for n,c in read(row['truth_payload'])['node_occupancy'].items()};assert [t['node'] for t in f['node_terms']]==sorted(channels);raw={n:[0]*d for n,d in cards.items()};constant=0;nonlinear=[];scopes=defaultdict(list)
  for t in f['node_terms']:
   n=t['node'];lo=fixed[n];hi=lo+len(patterns[n]);target=truth.get(n,0);assert (t['fixed_count'],t['upper_count'],t['target'])==(lo,hi,target);assert t['patterns']=={str(net):bits for net,bits in sorted(patterns[n].items())}
   if t['kind']=='affine_positive':
    assert lo>=target and all(abs(lo+k-target)==lo-target+k for k in range(hi-lo+1));constant+=lo-target;sign=1
   elif t['kind']=='affine_negative':
    assert lo<target and hi<=target and all(abs(lo+k-target)==target-lo-k for k in range(hi-lo+1));constant+=target-lo;sign=-1
   else:
    assert t['kind']=='nonlinear' and lo<target<hi;nonlinear.append(t);scopes[tuple(sorted(patterns[n]))].append(n);nodes_verified+=1;continue
   for net,bits in patterns[n].items():
    for i,bit in enumerate(bits):raw[net][i]+=sign*bit
   nodes_verified+=1
  shifts={n:min(costs) for n,costs in raw.items()};assert f['unary_shifts']=={str(n):x for n,x in shifts.items()};constant+=sum(shifts.values());assert constant==f['constant'] and constant>=0;assert f['unary']=={str(n):[x-shifts[n] for x in costs] for n,costs in raw.items()} and f['nonlinear']==nonlinear;assert p['nonlinear_scope_groups']==[{'NETs':list(s),'CHANNELs':ns} for s,ns in sorted(scopes.items())]
  for selected,loss in zip(p['test_assignments'],p['test_losses']):
   counts=Counter()
   for net,cs in pools.items():
    mask=cs[selected[str(net)]]
    while mask:bit=mask&-mask;counts[bit.bit_length()-1]+=1;mask-=bit
   original=sum(abs(counts[n]-truth.get(n,0)) for n in channels);reduced=constant+sum(costs[selected[net]] for net,costs in f['unary'].items())+sum(abs(t['fixed_count']+sum(bits[selected[net]] for net,bits in t['patterns'].items())-t['target']) for t in nonlinear);assert original==reduced==loss;identities+=1
  symbolic=p['symbolic'];fixedvars={n for n,d in cards.items() if d==1};active=set(cards)-fixedvars;factors=[set(s)-fixedvars for s in scopes]+[{n}-fixedvars for n in cards];assert symbolic['fixed_NETs']==sorted(fixedvars);bagmax=1;sepmax=1;bagsum=0;sepsum=0;width=0
  for step in symbolic['steps']:
   buckets=defaultdict(set);edges=set()
   for scope in factors:
    for n in scope:buckets[n].update(scope)
    edges.update(combinations(sorted(scope),2))
   scores={n:[sum(pair not in edges for pair in combinations(sorted(buckets[n]-{n}),2)),cards[n]*prod(cards[x] for x in buckets[n]-{n}),len(buckets[n]-{n}),n] for n in active};chosen=min(active,key=lambda n:scores[n]);neighbors=buckets[chosen]-{chosen};assert step['NET']==chosen and step['minfill_score']==scores[chosen] and step['neighbors']==sorted(neighbors);fill=[list(pair) for pair in combinations(sorted(neighbors),2) if pair not in edges];assert step['fill_edges']==fill;sep=prod(cards[x] for x in neighbors);bag=sep*cards[chosen];assert step['separator_states']==sep and step['bag_states']==bag;bagmax=max(bagmax,bag);sepmax=max(sepmax,sep);bagsum+=bag;sepsum+=sep;width=max(width,len(neighbors));factors=[s for s in factors if chosen not in s]+[neighbors];active.remove(chosen)
  assert not active
  for key,value in [('largest_bag_states',bagmax),('largest_separator_states',sepmax),('sum_bag_states',bagsum),('sum_separator_states',sepsum),('induced_width',width)]:assert symbolic[key]==value and row[key]==value
  rows.append({key:row[key] for key in ['case','initializer','timing_policy','priority','constant','node_kind_counts','induced_width','largest_bag_states','largest_separator_states','sum_bag_states']});print(row['case'],row['initializer'],row['timing_policy'],row['priority'],'EXACT_REDUCTION_BUCKET_PASS',flush=True)
 assert len(rows)==72 and identities==576
 files=[source,Path(__file__),D/'protocol.json'];(D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL72_POINTWISE_AFFINE_IDENTITIES_UNARIES_AND_REDUCED_BUCKET_PLANS_VERIFIED','rows':rows,'CHANNEL_node_terms_verified':nodes_verified,'full_loss_test_assignments':identities,'bindings':{str(p):sha(p) for p in files},'target_payloads_read':True,'scope':'Same full objective/candidate universe exactly preserved; no numerical minimizer, global-optimum witness, prediction or performance claim.'},indent=2)+'\n');print('ALL72_EXACT_REDUCTIONS_VERIFIED',nodes_verified,identities)
if __name__=='__main__':main()
