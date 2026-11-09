"""Whole iteration physical replay with one original XML pass per design.
Root/branch/switch/endpoint and unique NET ledger; not native FULL per snapshot.
"""
import json,sys,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
C=R/'experiments/freecores_continuous_workflow_v1_2026-10-08';SRC=R/'experiments/freecores_native_iteration_capture_v1_2026-10-08';D=R/'experiments/freecores_iteration_conflict_audit_v1_2026-10-08';D.mkdir()
rp=SRC/'receipt.json';receipt=json.loads(rp.read_text());assert all(sha(k)==h for k,h in receipt['bindings'].items());assert len(receipt['rows'])==4 and all(x['status']=='ALL_ITERATIONS_CAPTURED_DISCRETE_TRAJECTORY_MATCH' and all(sha(k)==h for k,h in x['files'].items()) for x in receipt['rows']);dp=R/'experiments/freecores_native_trajectory_diagnosis_v1_2026-10-08/diagnosis.json';diag=json.loads(dp.read_text());assert all(sha(k)==h for k,h in diag['bindings'].items());bindings={str(x):sha(x) for x in [Path(__file__),rp,dp,R/'tools/audit_native_route.py']};results=[]
def parse(path):
 nets={};types={};arcs=defaultdict(set);connections=Counter();name=None;parents={};current=None;outgoing=None;source=None
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:
   name=m[2];assert name not in nets;nets[name]=set();parents={};current=None;outgoing=None;source=None
  m=NODE.match(line)
  if not m:
   assert not line.lstrip().startswith('Node:');continue
  assert name is not None;nid=int(m[1]);kind=m[2];switch=int(m[3]);assert nid not in types or types[nid]==kind;types[nid]=kind;nets[name].add(nid)
  if nid in parents and kind!='SINK':pass
  elif kind=='SOURCE':assert not parents;source=nid;parents[nid]=None
  else:
   assert current is not None and types[current]!='SINK';arcs[name].add((current,nid,outgoing))
   if kind=='SINK':connections[name,source,nid]+=1
   else:parents[nid]=current
  current=nid;outgoing=switch
 return dict(nets=nets,types=types,arcs=arcs,connections=connections)
for name in ['8051','xtea']:
 graph=C/'cold/rr'/name/'rr_graph.xml';assert sha(graph)==sha(C/'seed/rr'/name/'rr_graph.xml');bindings[str(graph)]=sha(graph)
 epfile=C/'cold/demand'/name/'endpoints.json';ep=json.loads(epfile.read_text());bindings[str(epfile)]=sha(epfile);required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);all_names=set(ep['net_names'].values());wanted=set();types={};parsed={}
 for mode in ['cold','seed']:
  row=next(x for x in receipt['rows'] if x['name']==name and x['mode']==mode);runs=[]
  for i in range(1,row['iterations']+1):
   path=SRC/name/mode/f'iteration_{i:03d}.route';frame=parse(path);assert Counter({k:v for k,v in frame['connections'].items() if k[0] in all_names})==required
   for nid,kind in frame['types'].items():assert nid not in types or types[nid]==kind;types[nid]=kind
   for arcs in frame['arcs'].values():wanted.update(arcs)
   runs.append(frame);bindings[str(path)]=sha(path)
  parsed[mode]=runs
 seedfile=SRC/name/'seed/seed.route';seed=parse(seedfile);bindings[str(seedfile)]=sha(seedfile);seednames={n for n,nodes in seed['nets'].items() if nodes};assert seednames
 for n in seednames:
  assert n in all_names
  for triple,count in required.items():
   if triple[0]==n:assert seed['connections'][triple]==count
 wanted.update(a for arcs in seed['arcs'].values() for a in arcs)
 for nid,kind in seed['types'].items():assert nid not in types or types[nid]==kind;types[nid]=kind
 nodes={};found=set();switches=set();stack=[]
 for event,el in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(el);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if el.tag=='switch' and parent=='switches':switches.add(int(el.get('id')))
  if el.tag=='node' and parent=='rr_nodes':
   nid=int(el.get('id'))
   if nid in types:assert el.get('type')==types[nid];nodes[nid]=dict(type=types[nid],capacity=int(el.get('capacity')),loc=dict(el.find('loc').attrib))
  if el.tag=='edge' and parent=='rr_edges':
   arc=tuple(int(el.get(k)) for k in ['src_node','sink_node','switch_id'])
   if arc in wanted:found.add(arc)
  if (el.tag,parent) in {('node','rr_nodes'),('edge','rr_edges'),('switch','switches')}:stack[-2].remove(el);el.clear()
  stack.pop()
 assert set(nodes)==set(types) and found==wanted and all(a[2] in switches for a in wanted) and all(n['capacity']>0 for n in nodes.values())
 arms={}
 for mode,frames in parsed.items():
  expected=next(x for x in diag['rows'] if x['name']==name)['cohorts']['fresh'][mode]['records'];rows=[];previous=None
  for i,(frame,stats) in enumerate(zip(frames,expected),1):
   owners=defaultdict(set)
   for net,used in frame['nets'].items():
    for node in used:owners[node].add(net)
   over={n:names for n,names in owners.items() if len(names)>nodes[n]['capacity']};assert len(over)==stats['overused_node_count'];conflicts=sorted({n for ns in over.values() for n in ns});changed=[] if previous is None else sorted(n for n in frame['nets'] if frame['arcs'].get(n,set())!=previous['arcs'].get(n,set()))
   # Identical printed tree is stronger than node union, but not proof of no reroute event.
   original_seed_same=sorted(n for n in seednames if frame['arcs'].get(n,set())==seed['arcs'].get(n,set()) and frame['nets'][n]==seed['nets'][n])
   data=dict(iteration=i,overused_node_count=len(over),overflow_units=sum(len(ns)-nodes[n]['capacity'] for n,ns in over.items()),conflicting_NET_count=len(conflicts),conflicting_NETs=conflicts,seeded_conflicting_NETs=sorted(set(conflicts)&seednames),printed_tree_changed_NET_count=len(changed),seeded_printed_tree_changed_NET_count=len(set(changed)&seednames),exact_original_seed_tree_count=len(original_seed_same),exact_original_seed_tree_NETs=original_seed_same)
   if len(over)<=10:data['tail_resources']=[dict(node=n,**nodes[n],owners=sorted(over[n]),seeded_owners=sorted(over[n]&seednames)) for n in sorted(over)]
   rows.append(data);previous=frame
  arms[mode]=rows
 result=dict(name=name,iterations=sum(len(x) for x in parsed.values()),all_complete_physical_endpoints_branch_XML_arc_switch_and_uniqueNET_occupancy_pass=True,all_overused_node_counts_equal_native_iteration_counters=True,seeded_NET_count=len(seednames),arms=arms)
 path=D/(name+'.json');path.write_text(json.dumps(result,indent=2)+'\n');bindings[str(path)]=sha(path);results.append(dict(name=name,iterations=result['iterations'],seeded_NET_count=len(seednames),all_overused_node_counts_equal_native_iteration_counters=True));print(name,'ALL PHYSICAL ITERATIONS PASS',result['iterations'],flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=results,scope='All 90 physical snapshots rooted branches/arcs/switches/complete source-sink multiplicities and original XML uniqueNET capacities; every overused-node count equals native log. No per-iteration native FULL/recovery-removal timing/nonconfigurable/pin identity closure admission. Exact printed tree persistence does not imply no reroute. Seeded owners in tail are correlation, not causal attribution. Diagnostics on previously observed cases, no unseen generalization or speed claim.'),indent=2)+'\n')
