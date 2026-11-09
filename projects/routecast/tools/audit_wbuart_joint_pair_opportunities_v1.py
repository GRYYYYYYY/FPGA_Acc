"""Input-defined pair graph and label-dependent twoNET descent availability only."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from NET_candidate_interactions_v1 import interactions
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_joint_pair_opportunities_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json';ind=source.parent/'independent_verification_v1.json';contract=E/'NET_candidate_interactions_contract_v1_2026-10-20/verification.json';assert read(ind)['metric_vectors']==216 and all(sha(p)==h for p,h in read(contract)['bindings'].items());files=[Path(__file__),source,ind,contract];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'status':'FROZEN_ALL72_INPUT_DEFINED_PAIR_GRAPH_AND_DESCENT_AVAILABILITY_AUDIT','pair_domain':'NET pair iff shared node belongs to union-minus-intersection of each NET recorded CHANNEL supports. Built without target counts. Nonedges have additive aggregate-count loss deltas and cannot escape a certified oneNET local optimum.','scan':'At already certified singleNET local point, examine every candidate combination for every input-defined pair. Exact integer aggregate L1; equal minima preserve old combination/then first strict minimum order. Record best pair choices and single/joint deltas. Do not apply any move or rescore quality.','scope':'Posthoc label-dependent opportunity diagnostic, not new predictor, twoNET local optimum, global optimum, rank improvement or capacity-feasible routing proof. No pair/case selection from target labels and no new routes.','bindings':bindings},indent=2)+'\n');rows=[];graphs={}
 for row in read(source)['rows']:
  assert row['solver_status']=='ONE_NET_LOCAL_OPTIMUM';ep=read(row['endpoint']);graph=ep['inputs']['graph']['path']
  if graph not in graphs:graphs[graph]=[int(e.get('sink_node')) for _,e in ET.iterparse(graph) if e.tag=='edge']
  dest=graphs[graph];channels={json.loads(x)['id'] for x in Path(row['resources']).read_text().splitlines()};out=Path(row['output']);initial=defaultdict(list);pools=defaultdict(list)
  def add(net,records):
   s=frozenset(dest[e] for q in records for e in q['answer']['physical_edge_ids'] if dest[e] in channels)
   if s not in pools[net]:pools[net].append(s)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for net,rs in sorted(initial.items()):add(net,rs)
  for rnd in read(out/'receipt.json')['rounds']:
   for event in rnd['events']:
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:add(event['net_id'],rs)
  g=interactions(pools);point=read(row['diagnostic_payload']);chosen={int(n):c for n,c in point['selected'].items()};counts=Counter(n for net,cs in pools.items() for n in cs[chosen[net]]);assert dict(counts)=={int(n):c for n,c in point['counts'].items()};truth={int(n):c for n,c in read(row['truth_payload'])['node_occupancy'].items()}
  def change(net,index):
   old,new=pools[net][chosen[net]],pools[net][index];return {n:(1 if n in new else -1) for n in old^new}
  def delta(changes):return sum(abs(counts[n]+d-truth.get(n,0))-abs(counts[n]-truth.get(n,0)) for n,d in changes.items())
  changes={net:[change(net,i) for i in range(len(cs))] for net,cs in pools.items()}
  assert all(delta(d)>=0 for ds in changes.values() for d in ds);pairs=[]
  for a,b,shared in g['pairs']:
   best=(chosen[a],chosen[b]);score=0
   for ia,da in enumerate(changes[a]):
    for ib,db in enumerate(changes[b]):
     combined=dict(da)
     for n,d in db.items():combined[n]=combined.get(n,0)+d
     value=delta(combined)
     if value<score:best,score=(ia,ib),value
   da,db=changes[a][best[0]],changes[b][best[1]]
   if score<0:assert best[0]!=chosen[a] and best[1]!=chosen[b] and delta(da)>=0 and delta(db)>=0
   pairs.append({'NETs':[a,b],'shared_variable_CHANNELs':shared,'current_choices':[chosen[a],chosen[b]],'best_choices':list(best),'joint_delta':score,'first_single_delta':delta(da),'second_single_delta':delta(db)})
  d=D/row['case']/row['initializer']/row['timing_policy']/row['priority'];d.mkdir(parents=True);p=d/'pair_graph_scan.json';p.write_text(json.dumps({'components':g['components'],'pairs':pairs},separators=(',',':'))+'\n');result={key:row[key] for key in ['case','initializer','timing_policy','priority','output','endpoint','resources','truth_payload']};result.update(local_point=row['diagnostic_payload'],payload=str(p),NETs=len(pools),variable_NETs=sum(bool(s) for s in g['variable'].values()),eligible_pairs=len(pairs),strict_joint_improvement_pairs=sum(x['joint_delta']<0 for x in pairs),best_joint_delta=min([x['joint_delta'] for x in pairs]+[0]),component_sizes=sorted([len(c) for c in g['components']],reverse=True));rows.append(result);print(row['case'],row['initializer'],row['timing_policy'],row['priority'],result['eligible_pairs'],result['strict_joint_improvement_pairs'],result['best_joint_delta'],flush=True)
  for path in [p,Path(row['diagnostic_payload']),out/'initial.json',out/'receipt.json',Path(row['endpoint']),Path(graph),Path(row['resources']),Path(row['truth_payload'])]:bindings[str(path)]=sha(path)
 assert len(rows)==72
 (D/'verification.json').write_text(json.dumps({'status':'ALL72_INPUT_PAIR_GRAPHS_AND_ONE_POINT_TWO_NET_OPPORTUNITIES_COMPUTED','rows':rows,'bindings':bindings,'independent_verification_pending':True,'moves_applied':False},indent=2)+'\n')
if __name__=='__main__':main()
