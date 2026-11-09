"""Replay first3 perNET CHANNEL deltas and independently check observed occupancy."""
import json,sys,math
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_early_net_observer_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def verify(folder,endpoint):
 ep=read(endpoint);nets={q['net_id'] for q in ep['connections']};expected=Counter(q['net_id'] for q in ep['connections']);trees={n:set() for n in nets};demand=Counter();phase='B';pending=None;counts=Counter();pins=defaultdict(set);orders=defaultdict(list);checks=0;acc={}
 for line in (folder/'early_net_trace.tsv').open():
  x=line.split();kind=x[0];it=int(x[1]);order=int(x[2]);net=int(x[3]);assert 1<=it<=3 and net in nets
  if kind=='C':
   assert phase=='A' and pending==(it,order,net);pin=int(x[4]);assert pin not in pins[it,net];pins[it,net].add(pin);assert len(x)==7 and math.isfinite(float(x[5])) and float(x[5])>=0 and 0<=float(x[6])<=1;counts['C']+=1;continue
  assert kind==phase;factor=float(x[4]);assert abs(factor-[0,.5,.65][it-1])<1e-7;n=int(x[5]);nodes={};
  for item in x[6:]:
   a,b,c,d=item.split(':');nid=int(a);assert nid not in nodes;nodes[nid]=(int(b),float(c),float(d))
  assert len(nodes)==n
  if kind=='B':assert set(nodes)==trees[net];pending=(it,order,net);orders[it].append((order,net));phase='A'
  else:
   assert pending==(it,order,net)
   for nid in trees[net]-nodes.keys():demand[nid]-=1
   for nid in nodes.keys()-trees[net]:demand[nid]+=1
   trees[net]=set(nodes);phase='B';pending=None
  for nid,(occ,history,pres) in nodes.items():
   assert demand[nid]==occ and occ>=1;assert history>=1 and math.isfinite(history);assert abs(pres-(1+factor*occ))<1e-6*max(1,pres);checks+=1
   if (it,nid) in acc:assert acc[it,nid]==history
   else:acc[it,nid]=history
   if it<=2:assert history==1
  counts[kind]+=1
 assert phase=='B' and counts['B']==counts['A']==3*len(nets) and counts['C']==3*len(ep['connections'])
 for it in (1,2,3):
  assert len(orders[it])==len(nets) and {n for o,n in orders[it]}==nets
  assert [o for o,n in orders[it]]==sorted(o for o,n in orders[it])
  for n in nets:assert pins[it,n]==set(range(1,expected[n]+1))
 return dict(NETs=len(nets),before_after_pairs=counts['B'],connection_observations=counts['C'],node_occupancy_cost_checks=checks)
def main():
 m=read(D/'manifest.json');cases=[m['cases'][0]]
 if (D/'targets_terminal.json').exists():cases+=read(D/'target_manifest.json')['cases']
 rows=[];bindings={str(Path(__file__).resolve()):sha(__file__)}
 for c in cases:
  folder=Path(c['output']);a=read(folder/'verification.json');assert a['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and all(sha(p)==h for p,h in a['bindings'].items());r=verify(folder,c['endpoint']);r['case']=c['case'];rows.append(r)
  for p in [folder/'early_net_trace.tsv',folder/'verification.json']:bindings[str(p)]=sha(p)
 name='all_case_early_trace_verification_v1.json' if len(cases)==4 else 'source_early_trace_verification_v1.json'
 with (D/name).open('x') as f:json.dump(dict(status='ALL_EARLY_NET_SUPPORT_OCCUPANCY_REPLAY_PRESENT_COST_AND_CONNECTION_COVERAGE_VERIFIED',rows=rows,bindings=bindings,scope='CHANNEL unit capacity multiplier and observed history consistency, not full native/nonconfigurable cost. Criticality/net_delay value coverage and finite domain checked, not independent STA. No hold export.'),f,indent=2)
 print(json.dumps(rows))
if __name__=='__main__':main()
