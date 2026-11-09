"""Input-only footprint of whole-NET fallback on constraint-unaffected A paths."""
import json,xml.parsers.expat as X
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_A_support_joint_CBS_v1_2026-10-21';A=D/'independent_verification_v1.json';V=D/'verification.json';a=json.loads(A.read_text());v=json.loads(V.read_text());assert all(sha(p)==h for p,h in a['bindings'].items());assert all(sha(p)==h for k in ['bindings','files'] for p,h in v[k].items());graph=next(Path(p) for p in v['bindings'] if p.endswith('.xml'));bindings={str(p):sha(p) for p in [A,V,graph,Path(__file__)]};jobs=[];wanted_nodes=set()
for item in a['rows']:
 if item['full_capacity_feasible_states']!=1:continue
 case=item['case'];mp=D/(case+'_full_candidate_v1.json');m=json.loads(mp.read_text());frame=Path(m['original_A_frame']);assert sha(frame)==v['bindings'][str(frame)];records=json.loads(frame.read_text())['records'];original={q['connection_id']:q for q in records};bindings[str(mp)]=sha(mp);bindings[str(frame)]=sha(frame)
 for net,path in m['repaired_tree_paths'].items():
  p=Path(path);r=json.loads(p.read_text());assert sha(p)==v['files'][str(p)]
  if r.get('kind')!='RAW_FEASIBLE_FALLBACK':continue
  nodes=set(r['extra_forbidden']);wanted_nodes.update(nodes);jobs.append((case,int(net),r,original,nodes));bindings[str(p)]=sha(p)
incoming={n:set() for n in wanted_nodes};stack=[];eid=0
def begin(tag,attrs):
 global eid
 parent=stack[-1] if stack else None;stack.append(tag)
 if tag=='edge' and parent=='rr_edges':
  node=int(attrs['sink_node'])
  if node in incoming:incoming[node].add(eid)
  eid+=1
def end(tag):assert stack.pop()==tag
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while block:=f.read(8*1024*1024):parser.Parse(block,False)
parser.Parse(b'',True);assert eid==8097539;rows=[]
for case,net,result,original,nodes in jobs:
 forbidden_edges=set().union(*(incoming[n] for n in nodes));counts=Counter()
 for q in result['connections']:
  before=original[q['connection_id']];assert before['net_id']==net;affected=bool(set(before['answer']['physical_edge_ids'])&forbidden_edges);changed=before['answer']['physical_edge_ids']!=q['physical_edge_ids'];counts['connections']+=1;counts['original_paths_directly_affected_by_extra_mask']+=affected;counts['original_paths_unaffected_by_extra_mask']+=not affected;counts['replaced_paths']+=changed;counts['replaced_unaffected_paths']+=(changed and not affected)
 rows.append({'case':case,'net_id':net,'extra_forbidden_CHANNELs':sorted(nodes),**counts})
assert all(sha(p)==h for p,h in bindings.items());out={'status':'WHOLE_NET_RAW_FALLBACK_FOOTPRINT_ON_ORIGINAL_A_PATHS_VERIFIED','rows':rows,'bindings':bindings,'scope':'Input-only exact physical-edge path changes versus original A, conditional on independently verified same fixed-A domain. Every original selected A tree already avoided fixed unselected support; only added CHANNEL masks need testing. Counts do not prove native-quality causality or that mixing untouched and rerouted paths would have consistent shared parents. No new routing or target-label-guided selection.'};(D/'fallback_footprint_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(sorted(rows,key=lambda r:-r.get('replaced_unaffected_paths',0))[:4],indent=2))
