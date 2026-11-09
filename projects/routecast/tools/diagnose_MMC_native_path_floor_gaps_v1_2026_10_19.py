"""Complete archived native paths versus frozen model additive-cost/hop floors."""
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
import json,hashlib,xml.etree.ElementTree as ET,re
R=Path(__file__).resolve().parents[1]
NET=re.compile(r'^\s*Net\s+(\d+)\s+\((.*)\)\s*$')
NODE=re.compile(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b.*?Switch:\s*(-?\d+)')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_native_path_floor_gap_diagnosis_v1_2026-10-19';O.mkdir(exist_ok=False);prior=R/'experiments/mmc_missing_owner_DAG_diagnosis_v1_2026-10-19/research_decision_v1.json';assert json.loads(prior.read_text())['status']=='ALL18_MISSING_OWNER_DAG_DECOMPOSITION_INDEPENDENTLY_VERIFIED';bindings={str(prior):sha(prior),str(Path(__file__).resolve()):sha(__file__)};needed=defaultdict(list);metadata={};floors={};plans=[]
 protocol={'cases':['episode_01','episode_02','episode_03'],'arms':['zero','forecast','preferred'],'target':'All115572 current exposed native source/sink connections in each of9 final physical routes, not risk-selected subset.','categories':['equal_cost_equal_hops','equal_cost_more_hops','higher_additive_cost'],'scope':'Frozen additive switch-Tdel units1e-18 seconds and lexicographic minimum hops; not STA/setup closure, calibrated probabilities or causal native work attribution. No alternative routing, parameters or selection.'};(O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 for case in protocol['cases']:
  ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());metadata[case]=meta;floors[case]={};idx=R/f'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/{case}/NET_contribution_indices.json';indices=json.loads(idx.read_text());nets=sorted({q['net_id'] for q in meta['connections']});assert len(nets)==len(indices)==55300
  for net,index in zip(nets,indices):needed[index].append((case,net))
  for p in [ep,idx]:bindings[str(p)]=sha(p)
 graph=Path(metadata['episode_01']['inputs']['graph']['path']);assert sha(graph)==metadata['episode_01']['graph_sha256'];switches={}
 for event,e in ET.iterparse(graph,events=('end',)):
  if e.tag=='switch':
   timing=e.find('timing');value=Fraction(timing.get('Tdel','0'))*10**18;assert value.denominator==1 and value>=0;switches[int(e.get('id'))]=int(value)
  if e.tag=='switches':break
 assert switches;bindings[str(graph)]=sha(graph)
 bank=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/NET_contributions.jsonl';receipt=json.loads((bank.parent/'receipt.json').read_text());assert sha(bank)==receipt['bindings'][str(bank)];bindings[str(bank)]=sha(bank)
 for line in bank.open():
  x=json.loads(line)
  for case,net in needed.get(x['index'],[]):
   assert x['net_id']==net
   for sink in x['sinks']:floors[case][net,sink]=(x['source'],tuple(x['support_distance'][str(sink)]),x['mode'])
 rows=[]
 for case in protocol['cases']:
  meta=metadata[case];targets={(q['net_id'],q['source'],q['sink']):q['connection_id'] for q in meta['connections']};assert len(targets)==115572;names={v:int(k) for k,v in meta['net_names'].items()}
  for arm in protocol['arms']:
   if arm=='preferred':base=R/f'experiments/mmc_preferred_NET_native_utility_v1_2026-10-19/{case}';proof=base/'verification.json'
   else:base=R/f'experiments/mmc_first_iteration_hint_utility_v1_2026-10-19/{case}/{arm}/cold';proof=base.parent/'verification.json'
   admitted=json.loads(proof.read_text());assert admitted['all_native_physical_and_canonical_pass'];route=base/'output.route';assert sha(route)==admitted['bindings'][str(route)];bindings[str(proof)]=sha(proof);bindings[str(route)]=sha(route);current=None;outgoing=None;source=None;net=None;labels={};seen=set();counts=Counter();by_mode=defaultdict(Counter);total_gap=0;extra_hops_equal_cost=0;output=O/f'{case}_{arm}.jsonl'
   with output.open('x') as f:
    for line in route.open():
     m=NET.match(line)
     if m:net=names[m[2]];labels={};current=None;source=None;outgoing=None
     m=NODE.match(line)
     if not m:continue
     node=int(m[1]);kind=m[2];switch=int(m[3])
     if kind=='SOURCE':assert not labels;source=node;labels[node]=(0,0)
     elif node in labels and kind!='SINK':pass
     else:
      assert current in labels and outgoing in switches;cost,hops=labels[current];actual=(cost+switches[outgoing],hops+1)
      if kind!='SINK':labels[node]=actual
      else:
       cid=targets[net,source,node];assert cid not in seen;seen.add(cid);expected_source,floor,mode=floors[case][net,node];assert source==expected_source and actual>=floor
       category='higher_additive_cost' if actual[0]>floor[0] else 'equal_cost_more_hops' if actual[1]>floor[1] else 'equal_cost_equal_hops';counts[category]+=1;by_mode[mode][category]+=1;total_gap+=actual[0]-floor[0]
       if actual[0]==floor[0]:extra_hops_equal_cost+=actual[1]-floor[1]
       f.write(json.dumps({'connection_id':cid,'net_id':net,'source':source,'sink':node,'native_cost_hops':actual,'model_floor_cost_hops':floor,'category':category,'model_mode':mode},separators=(',',':'))+'\n')
     current=node;outgoing=switch
   assert seen==set(range(115572));rows.append({'case':case,'arm':arm,'connections':len(seen),'categories':dict(counts),'by_model_mode':{k:dict(v) for k,v in by_mode.items()},'sum_additive_cost_gap_units_1e18':total_gap,'sum_extra_hops_when_cost_equal':extra_hops_equal_cost,'per_connection':str(output)});bindings[str(output)]=sha(output);print('PATH_FLOOR_GAPS',case,arm,dict(counts),flush=True)
 (O/'review.json').write_text(json.dumps({'status':'ALL9_COMPLETE_NATIVE_PATH_FLOOR_GAP_DIAGNOSTICS_PRODUCED','rows':rows,'bindings':bindings,'scope':protocol['scope'],'independent_verification_pending':True},indent=2)+'\n')
if __name__=='__main__':main()
