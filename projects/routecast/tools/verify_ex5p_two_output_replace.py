"""Independent entire candidate XML timing/capacity/parent and untouched-record audit."""
import json
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_two_output_replace_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());parent=root/'experiments/ex5p_swap_frontier_history_2026-10-06/receipt.json';old=json.loads(parent.read_text());diag=root/'experiments/ex5p_output_min_delay_2026-10-06/receipt.json';assert sha(parent)==p['parent_sha256']==r['parent_sha256'] and sha(diag)==p['diagnostic_sha256'] and sha(out/'protocol.json')==r['protocol_sha256'] and sha(root/'tools/trial_ex5p_two_output_replace.py')==r['source_sha256'];e=json.loads((root/'experiments/ex5p_placement_swap_2026-10-06/endpoints.json').read_text());g=Path(e['inputs']['graph']['path']);audit=ImmutableXMLAudit(g,r['graph_sha256']);ids,classes,switches,_=read(g);queries={q['connection_id']:q for q in e['connections']};prior={q['connection_id']:q for q in old['records']};minimum={q['query']['connection_id']:q for q in json.loads(diag.read_text())['records']};unions=defaultdict(set);parents=defaultdict(dict);seen=set()
for rec in r['records']:
 cid=rec['connection_id'];assert cid not in seen;seen.add(cid);q=queries[cid];assert all(rec[k]==v for k,v in q.items())
 if cid not in p['targets']:assert rec==prior[cid]
 else:assert rec['answer']['physical_edge_ids']==minimum[cid]['physical_edge_ids'] and rec['answer']['delay']==minimum[cid]['delay_integer']<prior[cid]['answer']['delay']
 node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;net=q['net_id']
 for eid in rec['answer']['physical_edge_ids']:
  edge=audit.graph.edges[eid];assert edge.source==node and edge.sink not in used;node=edge.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],edge.switch_id);incoming=(edge.source,eid);assert node not in parents[net] or parents[net][node]==incoming;parents[net][node]=incoming
 assert node==q['sink'] and delay==Fraction(rec['answer']['delay'],r['scale'])<=Fraction(1,10**9);unions[net].update(used)
ledger=Counter(n for used in unions.values() for n in used);assert seen==set(queries) and len(seen)==1916 and all(c<=audit.caps[n] for n,c in ledger.items());(out/'verification.json').write_text(json.dumps({'retained_connections':1916,'complete_connections':1916,'overflow_units':0,'multi_parent_nodes':0,'untouched_records_exact':True,'ledger':dict(ledger),'receipt_sha256':sha(out/'receipt.json'),'scope':'Entire originalXML1ns/parent/union capacity audit with two exact replacements; nativepin/FULL/STA required separately.'},indent=2)+'\n');print('verified1916jointpaths zerooverflow/parents')
