"""Original XML/Fraction RC audit of complete forward/bidirectional primitive outputs."""
import json,sys,math
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
name=sys.argv[1];D=R/'experiments/real_rr_bidirectional_single_sink_v1_2026-10-08'/name
def load(p):return json.loads(p.read_text())
def auth(d):
 for section in ['bindings','files']:
  for p,h in d.get(section,{}).items():assert sha(p)==h,p
r=load(D/'receipt.json');p=load(D/'protocol.json');auth(r);auth(p);assert r['bindings']==p['bindings']
epfile=next(Path(k) for k in r['bindings'] if k.endswith('/endpoints.json'));ep=load(epfile)
groups=defaultdict(list)
for q in ep['connections']:groups[q['net_id']].append(q)
selected={n:qs for n,qs in groups.items() if len({q['sink'] for q in qs})==1}
assert len(selected)==p['required_single_target_nets'] and sum(map(len,selected.values()))==p['required_single_target_connections']
graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,digest=read(graph)
assert digest==p['graph_sha256']==ep['graph_sha256']
scale=1
for n in ids:
 a,b=classes[n];scale=math.lcm(scale,(a*b/2).denominator)
for eid in range(len(xml.graph.edges)):
 e=xml.graph.edges[eid];scale=math.lcm(scale,arc_delay(classes,switches,ids[e.sink],e.switch_id).denominator)
assert scale==p['scale']
assert [row['phase'] for row in r['rows']]==['initial','round0','round1']
bindings={**r['bindings'],**r['files'],**{str(q):sha(q) for q in [Path(__file__),D/'receipt.json',D/'protocol.json',graph]}};rows=[]
for row in r['rows']:
 phase=row['phase'];prices={} if phase=='initial' else {int(n):v for n,v in load(next(Path(k) for k in r['bindings'] if k.endswith('/'+phase+'.json')))['prices'].items()}
 weight=0 if phase=='initial' else scale//(20*10**9)
 file=D/(phase+'.json');data=load(file);assert sha(file)==r['files'][str(file)];bindings[str(file)]=sha(file)
 changed=checked=0
 for mode in ['baseline','candidate']:
  assert set(data[mode])=={str(n) for n in selected}
  for n,qs in selected.items():
   result=data[mode][str(n)];assert result is not None,'Complete real-case reachability required'
   source=qs[0]['source'];sink=qs[0]['sink'];assert (result['source'],result['sink'])==(source,sink)
   u=source;seen={u};a,b=classes[ids[u]];delay=a*b/2;price=0
   assert xml.graph.nodes[u].capacity>0
   for eid in result['physical_edge_ids']:
    e=xml.graph.edges[eid];assert e.source==u and e.sink not in seen and xml.graph.nodes[e.sink].capacity>0
    u=e.sink;seen.add(u);delay+=arc_delay(classes,switches,ids[u],e.switch_id);price+=prices.get(u,0)
   assert u==sink and delay*scale==result['delay']
   assert result['delay']+weight*price==result['objective'];checked+=1
 for n in selected:
  a,b=data['baseline'][str(n)],data['candidate'][str(n)];assert a['objective']==b['objective']
  changed+=a['physical_edge_ids']!=b['physical_edge_ids']
 assert changed==row['changed_equal_objective_paths'] and row['all_minimum_objectives_equal']
 assert row['complete_nets']==len(selected) and row['complete_connections']==sum(map(len,selected.values()))
 rows.append(dict(phase=phase,physical_paths_checked=checked,changed_equal_objective_paths=changed,all_original_XML_fraction_RC_and_forward_destination_price_checks_pass=True))
assert all(sha(q)==h for q,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,complete_single_target_primitive_pass=True,scope='Complete selected single-target NET primitive under three frozen old model price contexts. Independent XML/Fraction RC and objective equality to original forward kernel; no full mixed-NET model, prospective feedback, HDL/native, paired timing or end-to-end gain proof.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
