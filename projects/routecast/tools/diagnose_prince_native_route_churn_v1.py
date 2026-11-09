"""Source/target native CHANNEL union changes by endpoint class, offline diagnosis."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from array import array
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_native_route_churn_v1_2026-10-20'
def native(route,physical,resources):
 sets={};name=None
 for line in route.read_text().splitlines():
  m=NET.match(line)
  if m:name=m[2];assert name not in sets;sets[name]=set()
  m=NODE.match(line)
  if m:assert name is not None;sets[name].add(int(m[1]))
 counts=Counter(n for nodes in sets.values() for n in nodes);assert dict(counts)=={int(n):v for n,v in json.loads(physical.read_text())['node_occupancy'].items()}
 return {name:nodes&resources for name,nodes in sets.items()}
def main():
 D.mkdir(exist_ok=False);bindings={str(Path(__file__)):sha(__file__)};rows=[];cache={}
 for width in [128,160]:
  base=E/'prince_native_cohort_v1_2026-10-20'/f'w{width}';source=base/'source';ep0=source/'pre_route_endpoints.json';oldmeta=json.loads(ep0.read_text());oldqueries={q['connection_id']:q for q in oldmeta['connections']};resourcesp=E/'prince_quality_domains_v1_2026-10-20'/f'w{width}'/'resources.jsonl';resources={x['id'] for x in map(json.loads,resourcesp.open())};graph=source/'rr_graph.xml';dest=array('I')
  for event,x in ET.iterparse(graph):
   if x.tag=='edge':dest.append(int(x.get('sink_node')))
   x.clear()
  old=native(source/'output.route',source/'physical_audit.json',resources)
  for p in [ep0,resourcesp,graph,source/'output.route',source/'physical_audit.json']:bindings[str(p)]=sha(p)
  for episode in [1,2,3]:
   case=f'w{width}/episode_{episode:02d}';t=base/f'episode_{episode:02d}';ep=t/'pre_route_endpoints.json';meta=json.loads(ep.read_text());assert meta['graph_sha256']==oldmeta['graph_sha256'];names={int(n):name for n,name in meta['net_names'].items()};dirty={names[q['net_id']] for q in meta['connections'] if (q['source'],q['sink'])!=(oldqueries[q['connection_id']]['source'],oldqueries[q['connection_id']]['sink'])};allnames=set(names.values());target=native(t/'output.route',t/'physical_audit.json',resources);predictions={}
   for method,frame in [('allNET',E/'prince_feedback_cohort_v1_2026-10-20'/case/'native_retained/sketch.json'),('local',E/'prince_local_schedule_trial_v1_2026-10-20'/case/'sketch.json')]:
    f=json.loads(frame.read_text());assert f['graph_sha256']==meta['graph_sha256'];groups=defaultdict(set)
    for q in f['records']:groups[names[q['net_id']]].update(dest[eid] for eid in q['answer']['physical_edge_ids'] if dest[eid] in resources)
    counts=Counter(n for group in groups.values() for n in group);assert all(counts.get(n,0)==f['ledger'].get(str(n),0) for n in resources);predictions[method]=groups;bindings[str(frame)]=sha(frame)
   classes={}
   for role,group in [('endpoint_changed_NETs',dirty),('endpoint_unchanged_NETs',allnames-dirty)]:
    changed={name for name in group if old.get(name,set())!=target.get(name,set())};native_edits=sum(len(old.get(name,set())^target.get(name,set())) for name in group);methods={}
    for method,pred in predictions.items():
     pchanged={name for name in group if pred.get(name,set())!=old.get(name,set())};methods[method]=dict(predicted_changed_NETs=len(pchanged),native_changed_NETs_left_exactly_at_source=len(changed-pchanged),NETs_exactly_match_target=sum(pred.get(name,set())==target.get(name,set()) for name in group),NET_resource_symmetric_difference_from_target=sum(len(pred.get(name,set())^target.get(name,set())) for name in group))
    classes[role]=dict(NETs=len(group),native_changed_NETs=len(changed),native_NET_resource_symmetric_difference=native_edits,methods=methods)
   row=dict(case=case,classes=classes);rows.append(row)
   for p in [ep,t/'output.route',t/'physical_audit.json']:bindings[str(p)]=sha(p)
   print(case,classes['endpoint_unchanged_NETs'],flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Offline development-label diagnosis. All native union ledgers and candidate CHANNEL unions reconciled. PerNET CHANNEL set changes ignore branch order and are not path-equivalence proofs; perNET symmetric differences do not equal aggregate occupancy error due cancellation. Local scheduling preserves source for clean NETs but native cold rerouting may change them. No causal/generalization/native utility or physical timing claim.'),indent=2)+'\n')
if __name__=='__main__':main()
