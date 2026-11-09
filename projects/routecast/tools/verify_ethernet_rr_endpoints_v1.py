import json,sys,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha,placements
out=R/'experiments/ethernet_rr_only_v1_2026-10-08';rp=out/'receipt.json';r=json.loads(rp.read_text());assert r['status']=='GRAPH_AND_ENDPOINTS_CAPTURED' and r['exit_code']==1 and all(sha(k)==v for k,v in r['bindings'].items()) and all(sha(k)==v for k,v in r['files'].items());epfile=out/'endpoints.json';mf=out/'mapping.json';ep=json.loads(epfile.read_text());mapping=json.loads(mf.read_text());graph=out/'rr_graph.xml';assert sha(graph)==ep['graph_sha256'] and all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values());place=placements(out/'design.place',sha(out/'design.net'));excluded={x['net_id'] for x in ep['excluded_nets']};assert ep['clock_policy']=='exclude_root_clocks';sources={};sinks=Counter();nodes={};wanted={p['rr_node'] for p in mapping['pin_details']};stack=[]
for event,el in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(el);continue
 if el.tag=='node' and int(el.get('id')) in wanted:
  n=int(el.get('id'));assert n not in nodes;nodes[n]=(el.get('type'),int(el.get('capacity')),dict(el.find('loc').attrib))
 if el.tag in {'node','edge'}:
  if len(stack)>1:stack[-2].remove(el)
  el.clear()
 stack.pop()
assert set(nodes)==wanted
for p in mapping['pin_details']:
 typ,cap,loc=nodes[p['rr_node']];assert typ==p['role'] and cap>0 and int(loc['ptc'])==p['class_id'];x,y,z,layer,bid=place[p['block']];assert bid==p['block_id'] and int(loc.get('layer','0'))==layer and int(loc['xlow'])<=x<=int(loc['xhigh']) and int(loc['ylow'])<=y<=int(loc['yhigh']);assert ep['net_names'][str(p['net_id'])]==p['net']
 if p['net_id'] in excluded:continue
 if typ=='SOURCE':assert p['net_id'] not in sources or sources[p['net_id']]==p['rr_node'];sources[p['net_id']]=p['rr_node']
 else:assert typ=='SINK';sinks[p['net_id'],p['rr_node']]+=1
queries=ep['connections'];assert [q['connection_id'] for q in queries]==list(range(len(queries))) and Counter((q['net_id'],q['sink']) for q in queries)==sinks and all(q['source']==sources[q['net_id']] for q in queries);assert len(queries)==r['connections']==mapping['connections']==42202 and not list(out.glob('*.route'));bindings={str(p):sha(p) for p in [Path(__file__),rp,epfile,mf,graph,out/'design.net',out/'design.place']};(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,connections=len(queries),physical_endpoint_nodes=len(nodes),complete_manifest_query_partition_and_original_XML_node_type_class_capacity_bbox_pass=True,scope='Independent original XML endpoint node attributes and full mapping-manifest/query coverage. Manifest extraction itself reused frozen frontend; not a second logical-to-physical pin-name/site equivalence proof. Constants ignored scope still requires native pre-route identity. No native routing/HDL/timing/heldout/netgain gate.'),indent=2)+'\n');print('PASS original XML endpoints',len(queries),len(nodes))
