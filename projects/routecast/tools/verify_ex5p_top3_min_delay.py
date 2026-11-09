"""Independent originalXML witnesses and all-admissible-edge minimum certificates."""
import json
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_top3_min_delay_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());parent=root/'experiments/ex5p_critical_coupled2_2026-10-06/receipt.json';prior=json.loads(parent.read_text());ep=root/'experiments/ex5p_placement_swap_2026-10-06/endpoints.json';e=json.loads(ep.read_text());assert sha(parent)==p['parent_sha256']==r['parent_sha256'] and sha(ep)==p['endpoint_sha256'] and sha(out/'protocol.json')==r['protocol_sha256'] and sha(root/'tools/diagnose_ex5p_top3_min_delay.py')==r['source_sha256'];target=root/'experiments/ex5p_top3_complete_cohort_2026-10-06/receipt.json';assert sha(target)==p['targets_sha256'];assert [x['query']['connection_id'] for x in r['records']]==p['query_ids'];g=Path(e['inputs']['graph']['path']);audit=ImmutableXMLAudit(g,r['graph_sha256']);ids,classes,switches,_=read(g);scale=r['scale'];edges=[]
for eid in range(len(audit.graph.edges)):
 x=audit.graph.edges[eid];inc=arc_delay(classes,switches,ids[x.sink],x.switch_id)*scale;assert inc.denominator==1;edges.append((x.source,x.sink,int(inc)))
unions=defaultdict(set);parents=defaultdict(dict);old={x['connection_id']:x for x in prior['records']};queries={x['connection_id']:x for x in e['connections']}
for rec in prior['records']:
 net=rec['net_id'];unions[net].add(rec['source'])
 for eid in rec['answer']['physical_edge_ids']:u,v,inc=edges[eid];unions[net].add(v);parents[net][v]=(u,eid)
checks=0;improvements=[]
for rec in r['records']:
 q=rec['query'];assert q==queries[q['connection_id']];other={int(k):c-int(int(k) in unions[q['net_id']]) for k,c in prior['ledger'].items()};other={k:c for k,c in other.items() if c};assert other=={int(k):c for k,c in rec['other_demand'].items()};potential=rec['potential_integer'];assert len(potential)==len(audit.caps) and all(type(x) is int and x>=0 for x in potential);node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;assert potential[node]==delay*scale and other.get(node,0)<audit.caps[node];conflicts=[]
 for eid in rec['physical_edge_ids']:
  u,v,inc=edges[eid];assert node==u and v not in used and other.get(v,0)<audit.caps[v];node=v;used.add(v);delay+=Fraction(inc,scale)
  if v in parents[q['net_id']] and parents[q['net_id']][v]!=(u,eid):conflicts.append(v)
 assert node==q['sink'] and delay*scale==rec['delay_integer']==potential[node] and delay<=Fraction(1,10**9);assert sorted(conflicts)==sorted(rec['own_tree_parent_conflicts']);assert rec['old_delay_integer']==old[q['connection_id']]['answer']['delay']>=rec['delay_integer']
 for u,v,inc in edges:
  if other.get(u,0)<audit.caps[u] and other.get(v,0)<audit.caps[v]:assert potential[v]<=potential[u]+inc;checks+=1
 improvements.append({'connection_id':q['connection_id'],'reduction_ns':float(Fraction(rec['old_delay_integer']-rec['delay_integer'],scale))*1e9,'own_parent_conflicts':len(conflicts)})
(out/'verification.json').write_text(json.dumps({'queries_checked':len(improvements),'admissible_edge_inequalities_checked':checks,'improvements':improvements,'receipt_sha256':sha(out/'receipt.json'),'scope':'Each originalXML exact buffered minimum certified under its frozenother demand; candidates independent, own-tree conflicts recorded. No joint capacity/nativequality or routepublication proof.'},indent=2)+'\n');print('certified',len(improvements),'minimum paths;',checks,'edge inequalities')
