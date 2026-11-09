"""Two-hop output checked against explicit directed walk enumeration."""
import json,random
from pathlib import Path
from endpoint_graph_signals_v1 import extract,COLUMNS
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def main():
 rng=random.Random(20261020);walks=0
 for trial in range(300):
  ids=[3+7*i for i in range(rng.randrange(2,9))];edges=[(rng.choice(ids),rng.choice(ids)) for _ in range(rng.randrange(25))];queries=[];nets={};cid=0
  for net in range(rng.randrange(1,5)):
   source=rng.choice(ids);fanout=rng.randrange(1,5);nets[net]={'source_RR':source,'fanout':fanout,'endpoint_bbox':[0,1,2+net,4]}
   for _ in range(fanout):queries.append({'connection_id':cid,'net_id':net,'source':source,'sink':rng.choice(ids)});cid+=1
  actual=extract(ids,edges,queries,nets);base={n:[0]*5 for n in ids}
  for net,info in nets.items():base[info['source_RR']][0]+=1;base[info['source_RR']][2]+=info['endpoint_bbox'][2]+5
  for q in queries:base[q['source']][1]+=1;base[q['sink']][3]+=1;base[q['sink']][4]+=nets[q['net_id']]['endpoint_bbox'][2]+5
  expected={n:list(v)+[0]*10 for n,v in base.items()}
  for a,b in edges:
   walks+=1
   for k in range(3):expected[b][5+k]+=base[a][k]
   for k in range(2):expected[a][11+k]+=base[b][3+k]
   for c,d in edges:
    if b==c:
     walks+=1
     for k in range(3):expected[d][8+k]+=base[a][k]
     for k in range(2):expected[a][13+k]+=base[d][3+k]
  assert expected==actual and all(len(v)==len(COLUMNS) for v in actual.values())
 rejected=0
 for args in [([1,1],[],[],{}),([1],[(1,2)],[],{}),([1],[],[],{1:{}})]:
  try:extract(*args)
  except ValueError:rejected+=1
  else:raise AssertionError('bad domain accepted')
 D=R/'experiments/endpoint_graph_signals_contract_v1_2026-10-20';D.mkdir(exist_ok=False);paths=[Path(__file__),R/'tools/endpoint_graph_signals_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL300_DIRECTED_MULTIGRAPH_EXPLICIT_WALK_REFERENCES_PASS','graphs':300,'walks':walks,'invalid_rejections':rejected,'columns':COLUMNS,'bindings':{str(p):sha(p) for p in paths},'scope':'Integer unnormalized messages, counting parallel edges and self loops. No learned weights or target features.'},indent=2)+'\n');print('ENDPOINT_SIGNALS_CONTRACT_PASS',walks)
if __name__=='__main__':main()
