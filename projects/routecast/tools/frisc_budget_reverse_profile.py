"""Fixed-query equivalence of full versus budget-radius reverse lower bounds."""
import json,time,importlib.util
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from budget_pin_candidates import BudgetPins
from buffered_delay_cost import BufferedDelayCost
from net_pressure_sketch import net_union
out=Path('experiments/frisc_budget_reverse_profile_2026-10-05')
if out.exists():raise ValueError('fresh output required')
oldsrc='experiments/frisc_budget_span_net49_2026-10-05/search.py';spec=importlib.util.spec_from_file_location('budget_full_reverse',oldsrc);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);paths={'graph':'work/frisc_graph_capture_2026-10-05/rr_graph.xml','prediction':'experiments/frisc_shared_trunk_gated_candidate_2026-10-05/prediction.json','old_search':oldsrc,'new_search':'tools/budget_pin_candidates.py'};inputs={p:sha(p) for p in paths.values()};g=read_rr_graph(paths['graph']);full=module.BudgetPins(g);trimmed=BudgetPins(g);model=BufferedDelayCost(g);pred=json.loads(Path(paths['prediction']).read_text());rows=sorted((r for r in pred['connections'] if r['net_id']==49),key=lambda r:r['connection_id']);users,demand=net_union(g,pred);blocked={n for n,node in g.nodes.items() if node.type in {'CHANX','CHANY'} and demand.get(n,0)-int(n in users[49])>=node.capacity};incoming=defaultdict(list);span={}
for eid,edge in enumerate(g.edges):incoming[edge.sink].append(eid)
for n,node in g.nodes.items():
 loc=dict(node.location);span[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1 if node.type in {'CHANX','CHANY'} else 0
factor=(len(g.nodes)-1)*max(span.values())+1;reports=[]
for index in (0,52,103):
 old=rows[index];other=[r for r in rows if r['connection_id']!=old['connection_id']];edges={eid for r in other for eid in r['physical_edge_ids']};built={g.edges[e].sink for e in edges};parents={g.edges[e].sink:e for e in edges};forbidden={e for node,parent in parents.items() for e in incoming[node] if e!=parent};costs=[span[edge.sink]*(1+(0 if edge.sink in built else factor)) for edge in g.edges];w=full.catalog.witness(old['source'],old['sink'],old['physical_edge_ids']);budget=sum(model.weights[e] for e in old['physical_edge_ids']);results={};record={'index':index,'cid':old['connection_id']}
 for name,engine in [('full',full),('budget_radius',trimmed)]:
  t=time.monotonic();r=engine.query(old['source'],old['sink'],w['selected_opin_ptc'],w['selected_ipin_ptc'],costs,model.weights,budget,blocked,forbidden);record[name]={k:r[k] for k in ('status','cost','delay','labels_created','labels_expanded','reverse_settled_nodes','reverse_examined_edges')};record[name]['query_s']=time.monotonic()-t;results[name]=r
 assert all(results['full'][k]==results['budget_radius'][k] for k in ('status','path','cost','delay','labels_created','labels_expanded'));record['selected_path_cost_delay_and_forward_labels_exact']=True;reports.append(record);print(json.dumps(record),flush=True)
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());r={'reports':reports,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'scope':'3 fixed real queries with retained trunk, exact result/forward-label equality; concurrent shared host query timing excludes frontend/ledger/native and is not end-to-end or hardware speed'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
