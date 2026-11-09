"""Train-only domain adapter and cached binary-point ranking scorer."""
import json
from fractions import Fraction as F
from pathlib import Path
from direct_rank_objective_v1 import components, objective

def read(p):return json.loads(Path(p).read_text())

def doubled_ranks(values):
 order=sorted(range(len(values)),key=lambda i:values[i]);ranks=[0]*len(values);i=0
 while i<len(order):
  j=i+1
  while j<len(order) and values[order[j]]==values[order[i]]:j+=1
  for k in order[i:j]:ranks[k]=i+j-1
  i=j
 return ranks

class BinaryDomain:
 def __init__(self,ids,truth,resource_capacities,memberships,bin_keys,bin_capacities,resource_k,spatial_k,controls):
  if ids!=sorted(set(ids)) or len(ids)!=len(truth) or len(ids)!=len(resource_capacities) or len(ids)!=len(memberships):raise ValueError('sorted aligned unique resource IDs required')
  if not ids or any(type(y) is not int or y not in (0,1) for y in truth) or any(c!=1 for c in resource_capacities):raise ValueError('binary truth/unit resource capacity required')
  if not bin_keys or len(bin_keys)!=len(set(bin_keys)) or len(bin_keys)!=len(bin_capacities) or any(type(c) is not int or c<=0 for c in bin_capacities):raise ValueError('unique bins/positive integer capacities required')
  if any(len(set(row))!=len(row) or any(type(j) is not int or not 0<=j<len(bin_keys) for j in row) for row in memberships):raise ValueError('invalid spatial incidence')
  if not 1<=resource_k<=len(ids) or not 1<=spatial_k<=len(bin_keys) or len(controls)!=2:raise ValueError('original K and two controls required')
  self.ids=ids;self.truth=truth;self.memberships=memberships;self.bin_keys=bin_keys;self.capacities=bin_capacities;self.rk=resource_k;self.sk=spatial_k;self.controls=controls
  center=len(ids)-1;self.centered_truth=[r-center for r in doubled_ranks(truth)];self.truth_variance=sum(x*x for x in self.centered_truth)
  self.target_resource_top=set(sorted(range(len(ids)),key=lambda i:(-truth[i],ids[i]))[:resource_k])
  totals=[0]*len(bin_keys)
  for y,row in zip(truth,memberships):
   for j in row:totals[j]+=y
  self.spatial_truth={key:F(y,c) for key,y,c in zip(bin_keys,totals,bin_capacities)}
 def score(self,points):
  if len(points)!=len(self.ids) or any(type(p) is not int or p not in (0,1) for p in points):raise ValueError('aligned binary point field required')
  n=len(points);q=sum(points);cross=n*sum(rank for rank,p in zip(self.centered_truth,points) if p);variance=n*q*(n-q)*self.truth_variance;rank=F(cross*abs(cross),variance) if variance else F(-2)
  selected=[i for i,p in enumerate(points) if p][:self.rk]
  if len(selected)<self.rk:selected.extend([i for i,p in enumerate(points) if not p][:self.rk-len(selected)])
  hits=F(len(self.target_resource_top.intersection(selected)),self.rk)
  totals=[0]*len(self.bin_keys)
  for p,row in zip(points,self.memberships):
   if p:
    for j in row:totals[j]+=1
  spatial={key:F(value,capacity) for key,value,capacity in zip(self.bin_keys,totals,self.capacities)}
  return (rank,hits,*components(spatial,self.spatial_truth,self.sk))

def load_training_domains(root,model,features,specs):
 """Only iterate explicit immutable model training_cases, never test_cases."""
 if len(model['training_cases'])!=6 or len(model['test_cases'])!=3 or set(model['training_cases'])&set(model['test_cases']):raise ValueError('original six/three disjoint fold required')
 result=[];paths=[]
 for case in model['training_cases']:
  f=features[case];spec=read(specs[case]);ids=read(f['resource_ids']);directory=Path(spec['domain_proof']).parent;rp=directory/'resources.jsonl';bp=directory/'spatial_bins.json';resources=list(map(json.loads,rp.read_text().splitlines()));byid={r['id']:r for r in resources};bins=read(bp);keys=[tuple(b['key']) for b in bins];index={key:i for i,key in enumerate(keys)};truth=read(spec['label_physical_audit'])['node_occupancy'];truth={int(k):v for k,v in truth.items()};domain=read(spec['domain_proof']);raw=spec['predictions']['raw_min_on']['frame'];sources=[spec['source_frame'],raw];controls=[]
  assert ids==sorted(byid)
  from verify_wbuart_best_support_ranking_v1 import normalize
  for path in sources:
   counts={int(k):v for k,v in read(path)['ledger'].items()};values=normalize(resources,bins,counts);target=normalize(resources,bins,truth);controls.append((*components(values['resource'],target['resource'],domain['resource_k']),*components(values['spatial'],target['spatial'],domain['spatial_k'])))
  obj=BinaryDomain(ids,[truth.get(i,0) for i in ids],[byid[i]['capacity'] for i in ids],[[index[tuple(k)] for k in byid[i]['bins']] for i in ids],keys,[b['capacity'] for b in bins],domain['resource_k'],domain['spatial_k'],controls)
  result.append((case,obj));paths.extend([specs[case],f['resource_ids'],rp,bp,spec['domain_proof'],spec['label_physical_audit'],*sources])
 return result,paths

def training_objective(domains,points):
 if len(domains)!=len(points):raise ValueError('one point field per case required')
 return objective([{'candidate':domain.score(field),'controls':domain.controls} for (_,domain),field in zip(domains,points)])
