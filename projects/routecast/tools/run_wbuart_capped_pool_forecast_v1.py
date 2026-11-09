"""Source-only exact expected capped occupancy; independent NET marginal law."""
import json,xml.etree.ElementTree as ET,math,time
from fractions import Fraction as F
from capped_independent_occupancy_v1 import moments
from pathlib import Path
from collections import defaultdict,Counter
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_capped_pool_forecast_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_prepared_map_replication_v1_2026-10-20/verification.json'
 # Metadata comes from the independently audited diagnostic inventory, not its labels or choices.
 inventory=E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json';rows=read(inventory)['rows'];assert len(rows)==72
 inputs=[{k:r[k] for k in ['case','initializer','timing_policy','priority','output','endpoint','resources']} for r in rows]
 manifest={'schema':'WBUART_SOURCE_ONLY_EXPECTED_CAPPED_POOL_V1','rows':inputs,'policy':'For each NET deduplicate complete recorded CHANNEL supports in initial and two rounds, including guard-rejected complete candidates. Uniform over distinct supports, independent across NETs; exact rational E[min(capacity, aggregate Bernoulli inclusion count)] per CHANNEL. This is not min(capacity,E[count]) or conditioning on feasible routes. No target, exact-diagnostic choice or label-derived parameter is read.','scope':'Forecast only; no capacity/legal-route admission. Candidate generation and query acquisition remain paid dependencies. All72 development configurations and original gates retained. Not an unseen-family result or algorithm novelty claim.','bindings':{str(Path(__file__)):sha(__file__),str(inventory):sha(inventory),str(R/'tools/capped_independent_occupancy_v1.py'):sha(R/'tools/capped_independent_occupancy_v1.py'),str(E/'capped_independent_occupancy_contract_v1_2026-10-20/verification.json'):sha(E/'capped_independent_occupancy_contract_v1_2026-10-20/verification.json')}}
 mp=D/'manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');graphs={};outputs=[];bindings={str(mp):sha(mp)}
 for r in inputs:
  tick=time.perf_counter();out=Path(r['output']);ep=read(r['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.get('sink_node')) for _,e in ET.iterparse(g) if e.tag=='edge']
  dest=graphs[g];channels={json.loads(x)['id'] for x in Path(r['resources']).read_text().splitlines()};pools=defaultdict(list);initial=defaultdict(list)
  def add(net,rs):
   support=frozenset(dest[e] for q in rs for e in q['answer']['physical_edge_ids'] if dest[e] in channels)
   if support not in pools[net]:pools[net].append(support)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for net,rs in sorted(initial.items()):add(net,rs)
  for rnd in read(out/'receipt.json')['rounds']:
   for event in rnd['events']:
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:add(event['net_id'],rs)
  probabilities=defaultdict(list)
  for choices in pools.values():
   hits=Counter(node for support in choices for node in support)
   for node,count in hits.items():probabilities[node].append(F(count,len(choices)))
  capacities={json.loads(line)['id']:json.loads(line)['capacity'] for line in Path(r['resources']).read_text().splitlines()}
  expected={node:moments(ps,capacities[node])['expected_capped_occupancy'] for node,ps in probabilities.items()}
  denominator=math.lcm(*(value.denominator for value in expected.values()));counts={node:int(value*denominator) for node,value in expected.items()}
  d=D/r['case']/r['initializer']/r['timing_policy']/r['priority'];d.mkdir(parents=True);p=d/'forecast.json';p.write_text(json.dumps({'schema':'EXACT_RATIONAL_CAPPED_CHANNEL_EXPECTATION_V1','label_dependent':False,'eligible_for_legal_route_commit':False,'denominator':denominator,'numerators':dict(counts),'NETs':len(pools),'distinct_patterns':sum(map(len,pools.values()))},separators=(',',':'))+'\n');outputs.append({**r,'forecast':str(p),'marginalization_and_input_load_seconds':time.perf_counter()-tick})
  for path in [p,out/'initial.json',out/'receipt.json',Path(r['endpoint']),Path(g),Path(r['resources'])]:bindings[str(path)]=sha(path)
  print('SOURCE_ONLY_CAPPED_FORECAST',len(outputs),r['case'],r['initializer'],r['timing_policy'],r['priority'],flush=True)
 (D/'forecasts_frozen.json').write_text(json.dumps({'status':'ALL72_SOURCE_ONLY_RATIONAL_FORECASTS_FROZEN_BEFORE_LABEL_EVALUATION','rows':outputs,'bindings':bindings,'target_payloads_read':False},indent=2)+'\n')
if __name__=='__main__':main()
