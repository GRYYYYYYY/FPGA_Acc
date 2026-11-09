"""Necessary fixed-budget terminal-IPIN capacity Hall diagnostic."""
import json,itertools,shutil
from pathlib import Path
from collections import defaultdict
from prepared_csr import read,U64,TYPES
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from rc_feasible_cost_region import RCFeasibleCostRegion
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';name='mult_6x6';out=base/'multiplier_rc_terminal_capacity_2026-10-06';out.mkdir();shutil.copyfile(Path(__file__),out/'source.py');parent=base/'multiplier_rc_repeated_sweeps_2026-10-06'/name;r=json.loads((parent/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['inputs_sha256'].items());assert all(sha(parent/n)==h for n,h in r['outputs_sha256'].items());pred=json.loads((parent/'iteration_4_prediction.json').read_text());budgets={x['connection_id']:x['scaled_integer_budget'] for x in json.loads((parent/'iteration_4_budgets.json').read_text())};m,f=read(base/'multiplier_family_length_switch_csr_2026-10-06'/name/'csr',pred['physical_graph_sha256']);rc=IntegerRC(ExactBufferedRC(f,*load(base/'multiplier_cw300_exact_buffered_rc_classes_2026-10-06'/name,pred['physical_graph_sha256'])));edges=[(u,f['dest_ranks'][i],rc.increments[i],int(f['costs'][i])) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0];region=RCFeasibleCostRegion(m['nodes'],edges);incoming=defaultdict(list)
for u in range(m['nodes']):
 for i in range(f['row_offsets'][u],f['row_offsets'][u+1]):
  if f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0:incoming[f['dest_ranks'][i]].append((u,i))
groups=defaultdict(dict)
for row in pred['connections']:
 sink=row['sink'];assert f['types'][sink]==TYPES['SINK'];arcs=incoming[sink];assert arcs and all(f['types'][u]==TYPES['IPIN'] for u,i in arcs);dist=region.distance(row['source']);possible={u for u,i in arcs if u in dist and rc.initial(row['source'])+dist[u]+rc.increments[i]<=budgets[row['connection_id']]};net=row['net_id'];old=groups[sink].get(net);groups[sink][net]=possible if old is None else old&possible
results=[]
for sink,nets in groups.items():
 items=sorted(nets);violations=[]
 if len(items)<=16:
  for count in range(1,len(items)+1):
   for subset in itertools.combinations(items,count):
    pins=set().union(*(nets[n] for n in subset));capacity=sum(f['capacities'][p] for p in pins)
    if capacity<count:violations.append({'nets':list(subset),'reachable_ipins':sorted(pins),'ipin_capacity':capacity,'required_distinct_net_uses':count})
  if violations:print(sink,violations[:3],flush=True)
 results.append({'sink':sink,'per_net_budget_feasible_terminal_ipins':{str(n):sorted(v) for n,v in nets.items()},'hall_violations':violations,'subset_enumeration_complete':len(items)<=16})
(out/'receipt.json').write_text(json.dumps({'parent_receipt_sha256':sha(parent/'receipt.json'),'source_sha256':sha(out/'source.py'),'groups':results,'scope':'Necessary terminal IPIN capacity condition for predictor raw-node endpoint model under fixed RC budget. Shortest delays currently computed with Python Dijkstra; independent full distance/rawXML verification needed. Not native pin-class feasibility or complete global routing proof.'},indent=2)+'\n')
