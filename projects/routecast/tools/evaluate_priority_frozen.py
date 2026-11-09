"""Fixed capacity normalized resource/spatial metrics, complete cases only."""
from collections import defaultdict
from prediction_metrics import compare
from rr_graph import read_rr_graph
from stream_native_route_audit import audit

def evaluate(graph,route,candidate):
 if candidate['completed_connections']!=candidate['required_connections']:return dict(spatial=None,concrete=None,failure=candidate['failure']),None
 g=read_rr_graph(graph);native=audit(graph,route);pred={int(k):v for k,v in candidate['ledger'].items()};truth={int(k):v for k,v in native['node_occupancy'].items()};ids=sorted(n for n,x in g.nodes.items() if x.capacity>0 and x.type in ('CHANX','CHANY'));concrete=compare({n:pred.get(n,0)/g.nodes[n].capacity for n in ids},{n:truth.get(n,0)/g.nodes[n].capacity for n in ids},max(1,len(ids)//20));cap=defaultdict(int);pd=defaultdict(int);td=defaultdict(int)
 for n in ids:
  node=g.nodes[n];loc=dict(node.location)
  for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
   for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
    k=(int(loc.get('layer','0')),x,y,node.type,node.segment_id if node.segment_id is not None else -1);cap[k]+=node.capacity;pd[k]+=pred.get(n,0);td[k]+=truth.get(n,0)
 spatial=compare({k:pd[k]/v for k,v in cap.items()},{k:td[k]/v for k,v in cap.items()},20)
 vectors=dict(channels=[dict(node=n,capacity=g.nodes[n].capacity,predicted=pred.get(n,0),native=truth.get(n,0)) for n in ids],bins=[dict(key=list(k),capacity=cap[k],predicted=pd[k],native=td[k]) for k in sorted(cap)])
 return dict(spatial=spatial,concrete=concrete,failure=None),vectors
