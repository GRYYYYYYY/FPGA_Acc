"""Prior-XML proof transfer, printed-native node unions, exact bank enumeration."""
import pathlib,json,hashlib,itertools,xml.etree.ElementTree as ET
from collections import defaultdict,Counter
from native_route_ledger_import_compact import physical_paths
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_prior_native_budget_bank_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 protocol=json.loads((O/'protocol.json').read_text());result=json.loads((O/'results.json').read_text());cached={}
 def check(p,h):
  p=pathlib.Path(p)
  if str(p) not in cached:cached[str(p)]=sha(p)
  assert cached[str(p)]==h
 for p,h in protocol['bindings'].items():check(p,h)
 S=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18';sp=S/'independent_xml_verification_v1.json';proof=json.loads(sp.read_text());assert proof['all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass'] and proof['archived_native_canonical_semantic_pass'] and not proof['original_zero_counter_gate'] and proof['ignored_pin_fixups']==330
 source=S/'initial.json';check(source,proof['bindings'][str(source)]);frame=json.loads(source.read_text());source_records={q['connection_id']:q for q in frame['records']};geometry=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());route=pathlib.Path(geometry['previous_native_route']);old_ep=pathlib.Path(geometry['previous_endpoint']);check(route,proof['bindings'][str(route)]);check(old_ep,proof['bindings'][str(old_ep)]);old_metadata=json.loads(old_ep.read_text());target=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json';current={q['connection_id']:q for q in json.loads(target.read_text())['connections']};printed=physical_paths(route)
 graph=next(pathlib.Path(p) for p in protocol['bindings'] if p.endswith('rr_graph.xml'));assert sha(graph)==old_metadata['graph_sha256'];caps={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':caps[int(e.get('id'))]=int(e.get('capacity'));stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(caps)==904438;grouped=defaultdict(list)
 for q in source_records.values():
  if q['net_id'] in protocol['NETs']:grouped[q['net_id']].append(q)
 native_unions={};banks={};bindings={str(p):sha(p) for p in [O/'protocol.json',O/'results.json',source,sp,graph,route,old_ep,pathlib.Path(__file__).resolve()]};connections=0
 A=R/'experiments/mmc_complete_tree_bank_csr_v2_2026-10-19';B=R/'experiments/mmc_residual_capacity_group_v1_2026-10-19';transfers={str(A):json.loads((A/'independent_XML_verification_v1.json').read_text()),str(B):json.loads((B/'independent_verification_v1.json').read_text())}
 for net in protocol['NETs']:
  p=O/f'net_{net}_prior_native.json';tree=json.loads(p.read_text());refs=result['references'][str(net)];assert refs[3]==str(p);old=grouped[net];assert len(old)==len(tree['paths']);nodes=set();actual={};ids=[]
  native_by_sink={path[-1][0]:path for path in printed[old_metadata['net_names'][str(net)]]};assert len(native_by_sink)==len(old)
  for q in old:
   cid=q['connection_id'];ids.append(cid);assert all(current[cid][k]==q[k] for k in ['net_id','source','sink']);assert q['source']==tree['source'];sink=str(q['sink']);assert tree['paths'][sink]==q['answer']['physical_edge_ids'];actual[sink]=q['answer']['delay'];assert tree['sink_costs'][sink]==tree['sink_budgets'][sink]==actual[sink];path=native_by_sink[q['sink']];assert path[0][0]==q['source'];nodes.update(v for v,_ in path);connections+=1
  assert sorted(ids)==tree['connection_ids'] and sorted(nodes)==tree['unique_nodes'];native_unions[net]=nodes;banks[net]=[]
  for origin,ref in enumerate(refs):
   path=pathlib.Path(ref);candidate=json.loads(path.read_text());bindings[str(path)]=sha(path)
   if origin!=3:check(path,transfers[str(path.parent)]['bindings'][str(path)])
   else:assert candidate==tree
   costs=candidate.get('sink_costs') or {s:l[0] for s,l in candidate['sink_labels'].items()};assert costs.keys()==actual.keys();excess=sum(costs[s]-tree['sink_floors'][s] for s in costs);assert excess==candidate['excess'];bad=sum(costs[s]>actual[s] for s in costs);banks[net].append(dict(nodes=set(candidate['unique_nodes']),cost=excess,bad=bad))
  expected=next(r for r in result['rows'] if r['net_id']==net);assert [c['bad'] for c in banks[net]]==expected['prior_budget_violations_by_origin']
 external={int(v):n for v,n in frame['ledger'].items()}
 for nodes in native_unions.values():
  for v in nodes:external[v]-=1
 assert all(0<=n<=caps[v] for v,n in external.items());external={v:n for v,n in external.items() if n};fp=O/'fixed_prior_other_NET_occupancy.json';assert {str(v):n for v,n in external.items()}==json.loads(fp.read_text());bindings[str(fp)]=sha(fp);context_rows=[];nets=protocol['NETs']
 for name,fixed in [('isolated',{}),('full_prior',external)]:
  feasible=[]
  for origins in itertools.product(range(4),repeat=5):
   if any(banks[n][c]['bad'] for n,c in zip(nets,origins)):continue
   owners=defaultdict(set);cost=0
   for n,c in zip(nets,origins):
    cost+=banks[n][c]['cost']
    for node in banks[n][c]['nodes']:owners[node].add(n)
   if all(len(ns)+fixed.get(node,0)<=caps[node] for node,ns in owners.items()):feasible.append((cost,origins))
  assert feasible;answer=result['contexts'][name];assert answer['status']=='OPTIMAL_WITHIN_CANDIDATES' and answer['excess']==min(c for c,_ in feasible);chosen=tuple(answer['selected_origins'][str(n)] for n in nets);assert chosen in [m for c,m in feasible if c==answer['excess']];context_rows.append(dict(context=name,all_origin_combinations=1024,budget_and_capacity_legal_combinations=len(feasible),optimal_finite_bank_excess=answer['excess'],selected_origins=chosen));print(context_rows[-1],flush=True)
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='PRIOR_NATIVE_BUDGETS_PHYSICALLY_WITNESSED_AND_BOTH_BANK_OPTIMA_ENUMERATED',unchanged_connections=connections,NETs=5,contexts=context_rows,bindings=bindings,proof_method='Exact source-record paths and printed node unions transferred from bound full-source independent XML audit; candidate artifacts match their independent XML proofs. Original XML capacities reread; each4^5 Cartesian bank independently enumerated.',original_zero_counter_gate=False,ignored_pin_fixups=330,scope='Only selected unchanged NETs. Full-prior context is old-source placement, not full new-target layout; no full-graph joint optimality, predictor quality, native utility or end-to-end gain.'),f,indent=2)
if __name__=='__main__':main()
