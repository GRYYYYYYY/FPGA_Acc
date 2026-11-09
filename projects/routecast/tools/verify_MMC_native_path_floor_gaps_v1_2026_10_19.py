"""Independent native parent-chain walks and Decimal XML switch-cost readback."""
from pathlib import Path
from collections import defaultdict,Counter
from decimal import Decimal
import json,hashlib,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_native_path_floor_gap_diagnosis_v1_2026-10-19';review=O/'review.json';doc=json.loads(review.read_text());assert len(doc['rows'])==9;assert not (O/'independent_verification_v1.json').exists();bindings={str(review):sha(review),str(Path(__file__).resolve()):sha(__file__)};metadata={};floor={};needed=defaultdict(list)
 for case in ['episode_01','episode_02','episode_03']:
  ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());metadata[case]=meta;floor[case]={};nets=sorted({q['net_id'] for q in meta['connections']});idx=R/f'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/{case}/NET_contribution_indices.json';indices=json.loads(idx.read_text());assert len(indices)==len(nets)==55300
  for n,i in zip(nets,indices):needed[i].append((case,n))
  for p in [ep,idx]:assert sha(p)==doc['bindings'][str(p)];bindings[str(p)]=sha(p)
 graph=Path(metadata['episode_01']['inputs']['graph']['path']);assert sha(graph)==doc['bindings'][str(graph)];switches={}
 for event,e in ET.iterparse(graph,events=('end',)):
  if e.tag=='switch':
   raw=Decimal(e.find('timing').get('Tdel','0'))*Decimal(10)**18;assert raw==raw.to_integral_value() and raw>=0;switches[int(e.get('id'))]=int(raw)
  if e.tag=='switches':break
 bank=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/NET_contributions.jsonl';assert sha(bank)==doc['bindings'][str(bank)]
 for line in bank.open():
  x=json.loads(line)
  for case,net in needed.get(x['index'],[]):
   assert net==x['net_id']
   for sink in x['sinks']:floor[case][net,sink]=(x['source'],x['support_distance'][str(sink)],x['mode'])
 results=[]
 for row in doc['rows']:
  case,arm=row['case'],row['arm'];meta=metadata[case];names={v:int(k) for k,v in meta['net_names'].items()};targets={q['connection_id']:q for q in meta['connections']};records=Path(row['per_connection']);assert sha(records)==doc['bindings'][str(records)];expected={x['connection_id']:x for x in map(json.loads,records.read_text().splitlines())};assert set(expected)==set(targets)==set(range(115572));base=R/(f'experiments/mmc_preferred_NET_native_utility_v1_2026-10-19/{case}' if arm=='preferred' else f'experiments/mmc_first_iteration_hint_utility_v1_2026-10-19/{case}/{arm}/cold');route=base/'output.route';assert sha(route)==doc['bindings'][str(route)];actual={};parent={};source=None;net=None;previous=None;out_switch=None;cost_gap=0;hop_gap=0;categories=Counter();modes=defaultdict(Counter);key_to_cid={(q['net_id'],q['source'],q['sink']):cid for cid,q in targets.items()}
  for line in route.open():
   if line.lstrip().startswith('Net '):
    match=re.match(r'^\s*Net\s+\d+\s+\((.*)\)\s*$',line)
    if match:net=names[match[1]];parent={};source=None;previous=None;out_switch=None
    continue
   if not line.lstrip().startswith('Node:'):continue
   node=int(line.split()[1]);kind=line.split()[2];sw=int(re.search(r'\bSwitch:\s*(-?\d+)',line)[1])
   if kind=='SOURCE':assert not parent;source=node;parent[node]=None
   elif kind=='SINK':
    assert previous in parent and out_switch in switches;cost=switches[out_switch];hops=1;cursor=previous;visited=set()
    while cursor!=source:
     assert cursor not in visited;visited.add(cursor);up,switch=parent[cursor];cost+=switches[switch];hops+=1;cursor=up
    cid=key_to_cid[net,source,node];assert cid not in actual;actual[cid]=(cost,hops);e=expected[cid];fs,lower,mode=floor[case][net,node];assert fs==source and e['source']==source and e['sink']==node and e['net_id']==net and e['model_mode']==mode and e['model_floor_cost_hops']==lower;assert e['native_cost_hops']==[cost,hops] and (cost,hops)>=tuple(lower)
    category='higher_additive_cost' if cost>lower[0] else 'equal_cost_more_hops' if hops>lower[1] else 'equal_cost_equal_hops';assert e['category']==category;categories[category]+=1;modes[mode][category]+=1;cost_gap+=cost-lower[0]
    if cost==lower[0]:hop_gap+=hops-lower[1]
   elif node not in parent:assert previous in parent;parent[node]=(previous,out_switch)
   previous=node;out_switch=sw
  assert set(actual)==set(expected) and dict(categories)==row['categories'] and {k:dict(v) for k,v in modes.items()}==row['by_model_mode'];assert cost_gap==row['sum_additive_cost_gap_units_1e18'] and hop_gap==row['sum_extra_hops_when_cost_equal'];results.append({'case':case,'arm':arm,'all_connections_parent_chain_verified':len(actual),'categories':dict(categories),'exact_cost_gap_sum_verified':True});bindings[str(records)]=sha(records);bindings[str(route)]=sha(route);print('INDEPENDENT_PATH_CHAIN_PASS',case,arm,len(actual),flush=True)
 for p in [graph,bank]:bindings[str(p)]=sha(p)
 (O/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL9_1040148_NATIVE_PARENT_CHAINS_XML_COSTS_AND_ARCHIVED_FLOOR_JOINS_PASS','rows':results,'bindings':bindings,'scope':'Native path costs independently walked; model floor values joined to prior audited bank, not a new shortest-path optimality proof. No actual STA or causal gain claim.'},indent=2)+'\n')
if __name__=='__main__':main()
