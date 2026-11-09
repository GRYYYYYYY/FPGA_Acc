"""Label-free algebraic counterexample: endpoint marginals lose NET pairing."""
import json,math
from pathlib import Path
from types import SimpleNamespace as NS
from collections import Counter
from endpoint_graph_signals_v1 import extract
from endpoint_bbox_demand_v1 import predict
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def main():
 xy=[(0,1),(2,1),(1,2),(1,0),(0,3),(2,3),(0,2),(2,2),(0,3),(2,3)];edges=[(0,8),(8,4),(1,9),(9,5),(0,6),(0,7),(1,6),(1,7),(6,2),(6,3),(7,2),(7,3)];old=[{'connection_id':0,'full_connection_id':0,'net_id':0,'source':0,'sink':4},{'connection_id':1,'full_connection_id':1,'net_id':1,'source':1,'sink':5}];A=[dict(old[0],sink=2),dict(old[1],sink=3)];B=[dict(old[0],sink=3),dict(old[1],sink=2)];nodes={}
 for i,(x,y) in enumerate(xy):
  kind='SOURCE' if i<2 else 'SINK' if i<6 else 'CHANX';loc={'xlow':x,'xhigh':x,'ylow':y,'yhigh':y,'ptc':max(0,i-6)};nodes[i]=NS(type=kind,capacity=1,segment_id=0 if kind=='CHANX' else None,location=tuple(loc.items()))
 def vectors(queries):
  NETs={}
  for q in queries:
   a,b=xy[q['source']],xy[q['sink']];NETs[q['net_id']]={'source_RR':q['source'],'fanout':1,'endpoint_bbox':[min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])]}
  signals=extract(range(10),edges,queries,NETs);incoming=Counter(b for a,b in edges);outgoing=Counter(a for a,b in edges);result={};owner={8:0,9:1}
  for n in range(6,10):
   x,y=xy[n];ptc=n-6;static=[math.log1p(1),x,x,y,y,1,1,0,math.log1p(incoming[n]),math.log1p(outgoing[n]),math.log1p(n in owner)];track=[ptc,ptc/3,4,1,0];context=[0]*7
   if n in owner:
    net=owner[n];q=queries[net];before=old[net];changed=(q['source'],q['sink'])!=(before['source'],before['sink']);raw=[1,1,int(q['source']!=before['source']),int(q['sink']!=before['sink']),int(changed),int(changed),int(changed)];context=[math.log1p(v) if j in [0,1,3,4,5] else v for j,v in enumerate(raw)]
   result[n]=static+signals[n]+track+context;assert len(result[n])==38
  return result
 va,vb=vectors(A),vectors(B);assert va==vb and A!=B;ga,_=predict(nodes,A);gb,_=predict(nodes,B);key=(0,0,2,'CHANX',0);assert ga[key]==.25 and gb[key]==0
 D=R/'experiments/endpoint_pairing_information_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/endpoint_graph_signals_v1.py',R/'tools/endpoint_bbox_demand_v1.py',R/'experiments/wbuart_owner_delta_CART_design_v1_2026-10-20/protocol.json'];(D/'verification.json').write_text(json.dumps({'status':'DISTINCT_NET_PAIRINGS_IDENTICAL38_MARGINAL_FEATURES_DIFFERENT_EXISTING_BBOX_SIGNAL','old_queries':old,'placement_A_queries':A,'placement_B_queries':B,'fixed_edges':edges,'coordinates':xy,'CHANNEL_features_A':va,'CHANNEL_features_B':vb,'bbox_signal_witness':{'key':key,'A':ga[key],'B':gb[key]},'bindings':{str(p):sha(p) for p in files},'scope':'Algebraic fixed-multigraph feature counterexample only. No target labels, native FPGA route legality or claim that final occupancy differs. Full NET/RR incidence retains pairing; the derived pointwise38 vector does not. Existing unfitted bbox signal is not claimed novel or proven accurate.'},indent=2)+'\n');print('PAIRING_INFORMATION_COUNTEREXAMPLE_PASS')
if __name__=='__main__':main()
