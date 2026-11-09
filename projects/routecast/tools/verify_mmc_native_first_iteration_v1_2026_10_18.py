"""Independent full XML/tree/CID/native occupancy and unchanged V2 budget diagnostic."""
import json,math,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from array import array
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools')]
from pre_route_endpoints import sha
SCALE=10**18

def main():
 begin=time.perf_counter();root=R/'experiments/mmc_native_first_iteration_v1_2026-10-18';result=root/'results.json';capture=json.loads(result.read_text());assert capture['status']=='all3_first_iteration_captures_complete_physical_validation_pending';bindings={str(result):sha(result),str(Path(__file__).resolve()):sha(Path(__file__).resolve())};cases={};needed=set()
 for row in capture['cases']:
  case=row['case'];folder=root/case;rp=folder/'receipt.json';receipt=json.loads(rp.read_text());assert all(sha(k)==h for k,h in {**receipt['bindings'],**receipt['files']}.items());bindings.update(receipt['bindings']);bindings.update(receipt['files']);bindings[str(rp)]=sha(rp)
  trees=defaultdict(dict);native={};cap={};header=None
  with (folder/'states/round_1.tsv').open() as f:
   for line in f:
    x=line.split()
    if x[0]=='H':assert header is None;header=x;assert x==['H','1','0','0']
    elif x[0]=='N':
     n,occ,c=map(int,x[1:4]);assert n==len(cap) and occ>=0 and c>=0 and float(x[4])==1;cap[n]=c
     if occ:native[n]=occ
    elif x[0]=='T':
     net,node,parent,switch=map(int,x[1:5]);delay=float(x[5]);assert node not in trees[net] and math.isfinite(delay) and delay>=0;trees[net][node]=(parent,switch,delay)
     if parent>=0:needed.add((parent,node,switch))
    else:raise AssertionError('unknown state tag')
  assert len(cap)==904438 and len(trees)==55300
  ep=R/f'experiments/mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';endpoint=json.loads(ep.read_text());cvp=R/f'experiments/mmc_multiplacement_feedback_inputs_v1_2026-10-18/{case}/timing/verification.json';cv=json.loads(cvp.read_text());manifest=Path(cv['after_manifest']);assert Path(cv['after_endpoint']).resolve()==ep.resolve() and cv['all_endpoints_equal_after_placement'] and cv['bindings'][str(manifest)]==sha(manifest);assert cv['bindings'][str(ep)]==sha(ep)
  pins={}
  with manifest.open() as f:
   for line in f:
    x=line.split()
    if x[0]=='Q':cid,net,pin,source,sink=map(int,x[1:]);assert cid not in pins;pins[cid]=(net,pin,source,sink)
  queries={q['connection_id']:q for q in endpoint['connections']};assert len(queries)==len(pins)==115572 and set(queries)==set(pins);mapping={};reverse={}
  for cid,q in queries.items():
   n,p,s,t=pins[cid];assert (s,t)==(q['source'],q['sink']);assert mapping.setdefault(n,q['net_id'])==q['net_id'];assert reverse.setdefault(q['net_id'],n)==n
  assert set(mapping)==set(trees);warm=R/f'experiments/mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained/initial.json';budget={x['connection_id']:x['budget_integer'] for x in json.loads(warm.read_text())['records']};assert set(budget)==set(queries)
  for p in [ep,cvp,manifest,warm]:bindings[str(p)]=sha(p)
  cases[case]=dict(folder=folder,trees=trees,native=native,cap=cap,endpoint=endpoint,queries=queries,pins=pins,mapping=mapping,budget=budget)
 graph=Path(next(iter(cases.values()))['endpoint']['inputs']['graph']['path']);digest=sha(graph);assert all(c['endpoint']['graph_sha256']==digest for c in cases.values());bindings[str(graph)]=digest
 caps=array('I');kinds=[];classes=[];switches={};edges={};multiplicity=Counter();stack=[];edge_id=0
 print('FIRST_ITERATION_INDEPENDENT_XML_START',len(needed),flush=True)
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));t=e.find('timing');rr,cc=Fraction(t.get('R')),Fraction(t.get('C'));classes.append((rr,cc));assert rr>=0 and cc>=0
  elif e.tag=='switch' and parent=='switches':
   sid=int(e.get('id'));t=e.find('timing');assert e.get('type') in {'buffer','mux','tristate'} and Fraction(t.get('Cinternal','0'))==0;switches[sid]=(Fraction(t.get('R','0')),Fraction(t.get('Tdel','0')))
  elif e.tag=='edge' and parent=='rr_edges':
   key=tuple(int(e.get(k)) for k in ['src_node','sink_node','switch_id'])
   if key in needed:
    multiplicity[key]+=1
    if key not in edges:
     u,v,s=key;rr,cc=classes[v];sr,td=switches[s];cost=((sr+rr/2)*cc+td)*SCALE;assert cost.denominator==1;edges[key]=(edge_id,cost.numerator)
   edge_id+=1
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert edge_id==8097539 and len(caps)==904438 and set(edges)==needed;print('FIRST_ITERATION_XML_ALL_TREE_ARCS_PASS',len(edges),flush=True);rows=[]
 for case,c in cases.items():
  assert all(caps[n]==v for n,v in c['cap'].items());treeledger=Counter(n for tree in c['trees'].values() for n in tree);assert dict(treeledger)==c['native'];queries=c['queries'];records=[];owners=defaultdict(set);connectionledger=Counter();violations=[];checked_nodes=0;native_uncovered={};max_delta=0
  for net,tree in c['trees'].items():
   roots=[n for n,(p,s,t) in tree.items() if p<0];assert len(roots)==1 and kinds[roots[0]]=='SOURCE';rootnode=roots[0];assert tree[rootnode][2]==0;initial=classes[rootnode][0]*classes[rootnode][1]/2*SCALE;assert initial.denominator==1;delays={rootnode:initial.numerator}
   for node,(parent,switch,tdel) in tree.items():
    assert caps[node]>0
    if parent>=0:assert parent in tree and (parent,node,switch) in edges
    todo=[];u=node;seen=set()
    while u not in delays:
     assert u not in seen;seen.add(u);todo.append(u);u=tree[u][0];assert u in tree
    while todo:
     v=todo.pop();p,s,_=tree[v];delays[v]=delays[p]+edges[p,v,s][1]
    checked_nodes+=1
   c.setdefault('delays',{})[net]=delays
  for cid in sorted(queries):
   q=queries[cid];net,local,source,sink=c['pins'][cid];tree=c['trees'][net];assert source in tree and sink in tree and tree[source][0]<0 and kinds[sink]=='SINK';u=sink;path=[];seen={u}
   while u!=source:
    parent,switch,tdel=tree[u];assert parent>=0 and parent not in seen;path.append(edges[parent,u,switch][0]);seen.add(parent);u=parent
   path.reverse();delay=c['delays'][net][sink];budget=c['budget'][cid]
   if delay>budget:violations.append(dict(connection_id=cid,net_id=q['net_id'],delay_integer=delay,budget_integer=budget,excess_integer=delay-budget));max_delta=max(max_delta,delay-budget)
   owners[q['net_id']].update(seen);connectionledger.update(seen);records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=delay),budget_integer=budget))
  projected=Counter(n for ns in owners.values() for n in ns)
  for native_net,tree in c['trees'].items():
   logical=c['mapping'][native_net];extra=set(tree)-owners[logical]
   if extra:native_uncovered[native_net]=sorted(extra)
  residual={n:treeledger.get(n,0)-projected.get(n,0) for n in treeledger.keys()|projected.keys() if treeledger.get(n,0)!=projected.get(n,0)};assert all(v>0 for v in residual.values());overflow=sum(max(0,v-caps[n]) for n,v in projected.items());folder=c['folder'];sketch=folder/'diagnostic_sketch_v1.json';sketch.open('x').write(json.dumps(dict(status='DIAGNOSTIC_NATIVE_FIRST_ITERATION_DEMAND',records=records,scale=SCALE,required_connections=115572,completed_connections=len(records),ledger=dict(projected),independent_connection_ledger=dict(connectionledger),overflow_units=overflow,budget_policy='ORIGINAL_V2_BUDGETS_UNCHANGED_DIAGNOSTIC_VIOLATIONS_RETAINED',eligible_for_legal_route_commit=False),separators=(',',':'))+'\n');vp=folder/'budget_violations_v1.json';vp.open('x').write(json.dumps(violations,separators=(',',':'))+'\n');up=folder/'native_tree_uncovered_nodes_v1.json';up.open('x').write(json.dumps(native_uncovered,separators=(',',':'))+'\n')
  row=dict(case=case,all115572_current_CID_paths_and_original_XML_parent_switch_arcs_pass=True,all_native_N_occupancies_equal_full_T_uniqueNET_ledger=True,tree_nodes=checked_nodes,physical_query_projection_equals_native_ledger=not residual,native_uncovered_NETs=len(native_uncovered),native_residual_nodes=len(residual),budget_violations=len(violations),all_original_V2_budgets_pass=not violations,maximum_budget_excess_integer=max_delta,diagnostic_overflow_units=overflow,native_overflow_units=sum(max(0,v-caps[n]) for n,v in treeledger.items()),eligible_for_legal_route_commit=False);rows.append(row)
  for p in [sketch,vp,up]:bindings[str(p)]=sha(p)
  print('FIRST_ITERATION_CASE_PHYSICAL_AND_BUDGET_RESULT',json.dumps(row),flush=True)
 out=root/'physical_and_budget_verification_v1.json';out.open('x').write(json.dumps(dict(status='all3_first_iteration_full_XML_physical_identity_and_budget_diagnostics_complete',bindings=bindings,cases=rows,all_tree_arc_keys_found_in_original_XML=True,parallel_identical_arc_keys=sum(v>1 for v in multiplicity.values()),edge_selection='lowest physical edge ID among identical source/sink/switch arcs; tree snapshot cannot distinguish identical parallel edges',scope='Independent original XML and captured native parent/switch/occupancy reconstruction; no target final route read. Budget failures retained, no legal-route/native FULL/STA equivalence or accepted RC model promotion.',verification_seconds=time.perf_counter()-begin),indent=2)+'\n')
if __name__=='__main__':main()
