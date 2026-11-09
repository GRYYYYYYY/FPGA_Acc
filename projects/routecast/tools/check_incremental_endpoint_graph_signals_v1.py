"""Random NET transactions versus full rebuild, failure atomicity and lifetime."""
import json,random,copy
from pathlib import Path
from incremental_endpoint_graph_signals_v1 import State
from endpoint_graph_signals_v1 import extract
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def main():
 rng=random.Random(20261020);transactions=0;rejections=0;noop=0;visits=0
 for trial in range(200):
  nodes=list(range(rng.randrange(2,12)));edges=[(rng.choice(nodes),rng.choice(nodes)) for _ in range(rng.randrange(35))];records={};nextcid=0
  def fresh(net,existing=None):
   nonlocal nextcid
   source=rng.choice(nodes);count=rng.randrange(1,5);qs=[]
   for i in range(count):qs.append({'net_id':net,'source':source,'sink':rng.choice(nodes),'connection_id':nextcid});nextcid+=1
   return {'queries':qs,'feature':{'source_RR':source,'fanout':count,'endpoint_bbox':[0,0,rng.randrange(5),rng.randrange(5)]}}
  for net in range(3):records[net]=fresh(net)
  def full(records):return extract(nodes,edges,[q for r in records.values() for q in r['queries']],{n:r['feature'] for n,r in records.items()})
  state=State(nodes,edges,[q for r in records.values() for q in r['queries']],{n:r['feature'] for n,r in records.items()})
  for step in range(25):
   net=rng.randrange(7);remove=[net] if net in records and rng.randrange(4)==0 else [];upserts={} if remove else {net:(copy.deepcopy(records[net]) if net in records and rng.randrange(4)==0 else fresh(net))}
   # Include unchanged NET definitions alongside a changed one to exercise CID ownership.
   if rng.randrange(3)==0:
    for n,r in records.items():
     if n not in remove and n not in upserts:upserts[n]=copy.deepcopy(r);break
   old=copy.deepcopy(state.values);epoch=state.epoch;result=state.update(upserts,remove,epoch,epoch+1)
   for n in remove:records.pop(n)
   records.update(copy.deepcopy(upserts));assert state.values==full(records);expected=sorted(n for n in nodes if old[n]!=state.values[n]);assert expected==result['changed_RRs'];assert state.epoch==(epoch+1 if result['status']=='COMMITTED' else epoch);transactions+=1;visits+=result['edge_visits'];noop+=result['status']=='UNCHANGED'
   snapshot=copy.deepcopy((state.values,state.NETs,state.cid_owner,state.epoch))
   for args in [({},[],state.epoch-1,state.epoch),({},[999],state.epoch,state.epoch+1),({999:{'queries':[{'net_id':999,'connection_id':0,'source':999,'sink':0}],'feature':{'source_RR':999,'fanout':1,'endpoint_bbox':[0,0,1,1]}}},[],state.epoch,state.epoch+1)]:
    try:state.update(*args)
    except ValueError:rejections+=1
    else:raise AssertionError('bad transaction accepted')
    assert snapshot==(state.values,state.NETs,state.cid_owner,state.epoch)
 # Cross-NET CID collisions must fail without advancing epoch.
 qs=[{'net_id':0,'connection_id':0,'source':0,'sink':1}];feature={'source_RR':0,'fanout':1,'endpoint_bbox':[0,0,1,1]};state=State([0,1],[(0,1)],qs,{0:feature})
 try:state.update({1:{'queries':[dict(qs[0],net_id=1)],'feature':feature}},[],0,1)
 except ValueError:rejections+=1
 else:raise AssertionError('CID collision accepted')
 assert state.epoch==0
 D=R/'experiments/incremental_endpoint_signals_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/incremental_endpoint_graph_signals_v1.py',R/'tools/endpoint_graph_signals_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL5000_NET_TRANSACTIONS_FULL_REBUILD_AND15001_ATOMIC_REJECTIONS_PASS','transactions':transactions,'noops':noop,'rejections':rejections,'edge_visits':visits,'bindings':{str(p):sha(p) for p in files},'scope':'Fixed directed multigraph exact integer message updates, including inserts/deletes/noops/CID ownership/stale epochs. Not routing or predictor quality admission.'},indent=2)+'\n');print('INCREMENTAL_SIGNALS_CONTRACT_PASS',transactions,rejections,noop)
if __name__=='__main__':main()
