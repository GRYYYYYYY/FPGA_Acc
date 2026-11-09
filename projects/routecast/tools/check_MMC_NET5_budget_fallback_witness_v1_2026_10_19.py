"""Existing fallback on same fixed NET5; physical budget-feasible input-only witness."""
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
import json,hashlib,time,xml.parsers.expat as expat
from budget_actual_old_acceptance_undo_v2 import choose
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 begin=time.perf_counter();B=R/'experiments/mmc_existing_marginal_attachment_pilot_v1_2026-10-19';pp=B/'protocol.json';p=json.loads(pp.read_text());assert p['net_id']==5;O=R/'experiments/mmc_NET5_existing_budget_fallback_witness_v1_2026-10-19';O.mkdir(exist_ok=False);bank=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/NET_contributions.jsonl';assert sha(bank)==p['bindings'][str(bank)]
 for line in bank.open():
  row=json.loads(line)
  if row['net_id']==5 and row['first_case']=='episode_01':break
 else:raise RuntimeError('bank NET5 missing')
 assert row['source']==p['source'];labels={int(n):tuple(v) for n,v in row['support_distance'].items()};parents={int(n):min(map(tuple,v)) for n,v in row['support_choices'].items()};source=p['source'];paths={};edges={};required_nodes={source};budgets={int(n):v for n,v in p['budgets'].items()}
 for q in p['ordered_queries']:
  sink=q['sink'];node=sink;seen={node};path=[]
  while node!=source:
   up,edge=parents[node];assert labels[up][1]+1==labels[node][1];assert up not in seen;seen.add(up);path.append(edge);arc=(up,node)
   if edge in edges:assert edges[edge]==arc
   edges[edge]=arc;node=up
  paths[sink]=list(reversed(path));required_nodes.update(seen)
 graph=Path(next(n for n in p['bindings'] if n.endswith('rr_graph.xml')));assert sha(graph)==p['bindings'][str(graph)];(O/'protocol.json').write_text(json.dumps({'selection':'Same frozen NET5 and original41 budgets; first sorted archived model parent per node; no observed routing input.','purpose':'Distinguish heuristic budget rejection from actual absence of a budget-feasible single-NET tree.','source':source,'sinks':sorted(paths),'scope':'Input-only single-NET positive-capacity witness, not global cross-NET feasibility or predictor quality.'},indent=2)+'\n')
 tick=time.perf_counter();stack=[];switch_cost={};wanted_edges={};node_info={};edge_index=0;current_node=None
 def start(tag,a):
  nonlocal edge_index,current_node
  parent=stack[-1] if stack else None
  if tag=='switch' and parent=='switches':start.switch=int(a['id'])
  elif tag=='timing' and parent=='switch':switch_cost[start.switch]=Fraction(a.get('Tdel','0'))*10**18
  elif tag=='node' and parent=='rr_nodes':
   current_node=int(a['id'])
   if current_node in required_nodes:node_info[current_node]={'kind':a['type'],'capacity':int(a['capacity'])}
  elif tag=='timing' and parent=='node' and current_node in required_nodes:assert Fraction(a.get('R','0'))==Fraction(a.get('C','0'))==0
  elif tag=='edge' and parent=='rr_edges':
   if edge_index in edges:
    u,v,s=map(int,(a['src_node'],a['sink_node'],a['switch_id']));assert edges[edge_index]==(u,v);assert s in switch_cost;wanted_edges[edge_index]=(u,v,switch_cost[s])
   edge_index+=1
  stack.append(tag)
 def end(tag):assert stack.pop()==tag
 parser=expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
 with graph.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):parser.Parse(chunk,False)
 parser.Parse(b'',True);xml_seconds=time.perf_counter()-tick;assert set(wanted_edges)==set(edges) and set(node_info)==required_nodes and all(x['capacity']>0 for x in node_info.values());adj=defaultdict(list);caps={n:x['capacity'] for n,x in node_info.items()}
 for edge,(u,v,cost) in wanted_edges.items():assert cost.denominator==1;adj[u].append((edge,v,int(cost),0))
 tick=time.perf_counter();answer=choose(adj,source,budgets,paths,{s:[] for s in paths},0,caps);fallback_seconds=time.perf_counter()-tick;assert answer['paths']==paths and answer['status']=='RETAIN';assert set(answer['audit']['delays'])==set(budgets)
 for sink,raw in answer['audit']['delays'].items():assert raw==labels[sink][0] and raw<=budgets[sink]
 witness={'source':source,'paths':paths,'budgets':budgets,'delays':answer['audit']['delays'],'status':answer['status'],'search_status':answer['search_status'],'states':answer['states'],'unique_nodes':answer['audit']['unique_NET_nodes']};output=O/'witness.json';output.write_text(json.dumps(witness,indent=2)+'\n');files=[pp,bank,graph,Path(__file__).resolve(),R/'tools/budget_actual_old_acceptance_undo_v2.py',R/'tools/budget_NET_gate_reference_v1.py',R/'tools/budget_joint_candidates_undo_v3.py',output]
 (O/'verification.json').write_text(json.dumps({'status':'SAME_NET5_ALL41_SOURCE_ROOTED_OLD_PATHS_ORIGINAL_XML_BUDGETS_AND_EXISTING_FALLBACK_PASS','connections':len(paths),'physical_edges':len(edges),'nodes':len(required_nodes),'XML_edges_scanned':edge_index,'xml_audit_seconds':xml_seconds,'fallback_seconds':fallback_seconds,'total_before_receipt_seconds':time.perf_counter()-begin,'bindings':{str(f):sha(f) for f in files},'scope':'Constructive single-NET budget-feasible witness; plain marginal rejection is heuristic, not infeasibility. Reusing old-only candidates proves completeness preservation only, not replacement improvement, global capacity feasibility or criticality availability.'},indent=2)+'\n');print('NET5_XML_FALLBACK_WITNESS_PASS',len(paths),'connections',len(edges),'edges',flush=True)
if __name__=='__main__':main()
