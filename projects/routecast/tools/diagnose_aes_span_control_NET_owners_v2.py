"""Original physical-node owner sets on all frozen true-top20 support resources."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
out=R/'experiments/aes_feedback_round_ablation_v1_2026-10-08';p=out/'resource_strata_diagnosis.json';diagnosis=json.loads(p.read_text());assert all(sha(k)==v for k,v in diagnosis['bindings'].items());bindings={str(p):sha(p),str(Path(__file__)):sha(Path(__file__))};rows=[]
control_proof=R/'experiments/aes_native_demand_no_span_control_v1_2026-10-08/control_verification.json'
control=json.loads(control_proof.read_text());assert all(sha(k)==v for k,v in control['bindings'].items());bindings[str(control_proof)]=sha(control_proof)
for case in diagnosis['rows']:
 name=case['name'];targets={n for h in case['true_top20'] for n in h['physical_nodes']};epfile=R/'experiments/aes_native_demand_frontend_v1_2026-10-08'/name/'endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];route=R/'experiments/aes_mapped_fresh_cold_v2_2026-10-08'/name/'output.route'
 native=defaultdict(set);active=None
 for line in route.read_text().splitlines():
  m=NET.match(line)
  if m:active=m[2]
  m=NODE.match(line)
  if m and int(m[1]) in targets:assert active is not None;native[int(m[1])].add(active)
 # IDs are original rr_edges document-order positions, as in the frozen predictor.
 edge_targets={};eid=0;stack=[]
 for event,el in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(el);continue
  if el.tag=='edge' and len(stack)>1 and stack[-2].tag=='rr_edges':
   node=int(el.get('sink_node'))
   if node in targets:edge_targets[eid]=node
   eid+=1
  if el.tag in {'node','edge'}:
   if len(stack)>1:stack[-2].remove(el)
   el.clear()
  stack.pop()
 fanout=Counter(ep['net_names'][str(q['net_id'])] for q in ep['connections']);frames={};resident=R/'experiments/aes_native_demand_estimates_v1_2026-10-08'/name/'resident'
 for frame,root,file in [('initial',resident,'initial'),('span_round0',resident,'round0'),('span_round1',resident,'round1'),('no_span_round0',R/'experiments/aes_native_demand_no_span_control_v1_2026-10-08'/name/'resident','round0'),('no_span_round1',R/'experiments/aes_native_demand_no_span_control_v1_2026-10-08'/name/'resident','round1')]:
  path=root/(file+'.json');d=json.loads(path.read_text());assert len(d['records'])==len(ep['connections']);assert sorted((r['connection_id'],r['net_id'],r['source'],r['sink']) for r in d['records'])==sorted((q['connection_id'],q['net_id'],q['source'],q['sink']) for q in ep['connections']);owners=defaultdict(set)
  for rec in d['records']:
   net=ep['net_names'][str(rec['net_id'])]
   for edge in rec['answer']['physical_edge_ids']:
    if edge in edge_targets:owners[edge_targets[edge]].add(net)
  assert all(len(owners[n])==d['ledger'].get(str(n),0) for n in targets);frames[frame]=owners;bindings[str(path)]=sha(path)
 vector=out/name/'comparison_vectors.json';vs={x['node']:x for x in json.loads(vector.read_text())['channels']};assert all(len(native[n])==vs[n]['native'] for n in targets)
 node_rows=[]
 for node in sorted(targets):
  changes={}
  for frame,owners in frames.items():
   missing=native[node]-owners[node];extra=owners[node]-native[node];common=native[node]&owners[node]
   assert len(common)+len(missing)==len(native[node]) and len(common)+len(extra)==len(owners[node])
   changes[frame]=dict(predicted_owners=sorted(owners[node]),common=sorted(common),missing=sorted(missing),extra=sorted(extra))
  node_rows.append(dict(node=node,native_owners=sorted(native[node]),frames=changes))
 groups=[]
 for g in case['repeated_support_groups']:
  nodes=g['physical_nodes'];native_union=set().union(*(native[n] for n in nodes));states={}
  for frame,owners in frames.items():
   pred=set().union(*(owners[n] for n in nodes));missing=native_union-pred;extra=pred-native_union
   states[frame]=dict(predicted_NETs=sorted(pred),common_NETs=sorted(pred&native_union),missing_NETs=[dict(name=n,physical_fanout=fanout[n]) for n in sorted(missing)],extra_NETs=sorted(extra))
  groups.append(dict(keys=g['keys'],physical_nodes=nodes,native_NETs=sorted(native_union),frames=states))
 for p in [epfile,graph,route,vector]:bindings[str(p)]=sha(p)
 rows.append(dict(name=name,physical_support_nodes=len(targets),all_top20_node_owners=node_rows,repeated_support_group_NETs=groups))
assert all(sha(k)==v for k,v in bindings.items())
(out/'span_control_NET_owner_diagnosis.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='All physical resources supporting original true-top20 bins. Exact native NET union and per-frame original-edge destination NET owner sets agree with authenticated node ledgers. Missing owners means different selected resources, not dropped endpoint queries; no functional or native timing-cause claim. Previously observed candidates; no parameter fitting.'),indent=2)+'\n')
for r in rows:
 print(r['name'],r['physical_support_nodes'])
 for g in r['repeated_support_group_NETs']:print('repeated group native',len(g['native_NETs']),{f:(len(s['common_NETs']),len(s['missing_NETs']),len(s['extra_NETs'])) for f,s in g['frames'].items()})
