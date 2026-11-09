"""Independent quadratic variable-support graph and bitset twoNET delta replay."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from itertools import combinations
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_joint_pair_opportunities_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=D/'verification.json';v=read(source);assert all(sha(p)==h for p,h in v['bindings'].items());graphs={};rows=[];pair_total=0;combo_total=0
 for row in v['rows']:
  ep=read(row['endpoint']);path=ep['inputs']['graph']['path']
  if path not in graphs:graphs[path]=[int(e.get('sink_node')) for _,e in ET.iterparse(path) if e.tag=='edge']
  dest=graphs[path];channels={json.loads(x)['id'] for x in Path(row['resources']).read_text().splitlines()};pools=defaultdict(list);initial=defaultdict(list);out=Path(row['output'])
  def add(net,rs):
   mask=0
   for q in rs:
    for eid in q['answer']['physical_edge_ids']:
     node=dest[eid]
     if node in channels:mask|=1<<node
   if mask not in pools[net]:pools[net].append(mask)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for net,rs in sorted(initial.items()):add(net,rs)
  for rnd in read(out/'receipt.json')['rounds']:
   for event in rnd['events']:
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:add(event['net_id'],rs)
  variable={}
  for net,choices in pools.items():
   union=0;common=-1
   for mask in choices:union|=mask;common&=mask
   variable[net]=union&~common
  expected_pairs=[];adjacency={n:set() for n in pools}
  for a,b in combinations(sorted(n for n,mask in variable.items() if mask),2):
   shared=variable[a]&variable[b]
   if not shared:continue
   nodes=[]
   while shared:bit=shared&-shared;nodes.append(bit.bit_length()-1);shared-=bit
   expected_pairs.append((a,b,nodes));adjacency[a].add(b);adjacency[b].add(a)
  unseen=set(pools);components=[]
  while unseen:
   todo=[min(unseen)];unseen.remove(todo[0]);group=set()
   while todo:
    node=todo.pop();group.add(node)
    for n in adjacency[node]:
     if n in unseen:unseen.remove(n);todo.append(n)
   components.append(sorted(group))
  payload=read(row['payload']);assert components==payload['components'];assert [(p['NETs'][0],p['NETs'][1],p['shared_variable_CHANNELs']) for p in payload['pairs']]==expected_pairs;point=read(row['local_point']);chosen={int(n):c for n,c in point['selected'].items()};counts=Counter()
  for net,choices in pools.items():
   mask=choices[chosen[net]]
   while mask:bit=mask&-mask;counts[bit.bit_length()-1]+=1;mask-=bit
  assert dict(counts)=={int(n):c for n,c in point['counts'].items()};truth={int(n):c for n,c in read(row['truth_payload'])['node_occupancy'].items()}
  def delta(a,ia,b,ib):
   olda,oldb=pools[a][chosen[a]],pools[b][chosen[b]];newa,newb=pools[a][ia],pools[b][ib];mask=olda|oldb|newa|newb;value=0
   while mask:
    bit=mask&-mask;n=bit.bit_length()-1;after=counts[n]-int(bool(olda&bit))-int(bool(oldb&bit))+int(bool(newa&bit))+int(bool(newb&bit));value+=abs(after-truth.get(n,0))-abs(counts[n]-truth.get(n,0));mask-=bit
   return value
  strict=0;bestoverall=0
  for entry,(a,b,shared) in zip(payload['pairs'],expected_pairs):
   best=(chosen[a],chosen[b]);bestvalue=0
   for ia in range(len(pools[a])):
    for ib in range(len(pools[b])):
     value=delta(a,ia,b,ib);combo_total+=1
     if value<bestvalue:best,bestvalue=(ia,ib),value
   assert entry['current_choices']==[chosen[a],chosen[b]] and entry['best_choices']==list(best) and entry['joint_delta']==bestvalue;assert entry['first_single_delta']==delta(a,best[0],b,chosen[b]) and entry['second_single_delta']==delta(a,chosen[a],b,best[1]);assert entry['first_single_delta']>=0 and entry['second_single_delta']>=0
   strict+=bestvalue<0;bestoverall=min(bestoverall,bestvalue)
  assert len(expected_pairs)==row['eligible_pairs'] and strict==row['strict_joint_improvement_pairs'] and bestoverall==row['best_joint_delta'];pair_total+=len(expected_pairs);rows.append({key:row[key] for key in ['case','initializer','timing_policy','priority','eligible_pairs','strict_joint_improvement_pairs','best_joint_delta']});print(row['case'],row['initializer'],row['timing_policy'],row['priority'],'PAIR_GRAPH_DELTA_PASS',flush=True)
 assert len(rows)==72
 files=[source,Path(__file__),D/'protocol.json'];(D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL72_INPUT_GRAPHS_AND_TWO_NET_DELTA_WITNESSES_INDEPENDENTLY_VERIFIED','rows':rows,'eligible_pairs_verified':pair_total,'candidate_combinations_verified':combo_total,'bindings':{str(p):sha(p) for p in files},'scope':'Every eligible pair and combination at fixed oneNET local point only. No twoNET optimization run, rank gain or feasible routing certificate.'},indent=2)+'\n');print('ALL72_PAIR_OPPORTUNITIES_VERIFIED',pair_total,combo_total)
if __name__=='__main__':main()
