"""Independent XML event replay for staged placement-change reroute."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_top3_joint_repair_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());swap=root/'experiments/ex5p_placement_swap_2026-10-06';new=json.loads((swap/'endpoints.json').read_text());old=json.loads((root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json').read_text());priorpath=root/'experiments/ex5p_critical_coupled2_2026-10-06/receipt.json';prior=json.loads(priorpath.read_text());assert sha(priorpath)==p['prior_sha256'] and sha(swap/'endpoints.json')==p['moved_endpoint_sha256'] and sha(out/'protocol.json')==r['protocol_sha256'] and sha(root/'tools/trial_ex5p_top3_joint_repair.py')==r['source_sha256'];a={q['connection_id']:q for q in old['connections']};b={q['connection_id']:q for q in new['connections']};assert set(a)==set(b);changed=[c for c in a if a[c]!=b[c]];affected=set(p['affected_nets']);minimumfile=root/'experiments/ex5p_top3_empty_delay_2026-10-06/receipt.json';assert sha(minimumfile)==p['minimum_receipt_sha256'];minimum=json.loads(minimumfile.read_text());targets={cid:next(x for x in minimum['records'] if x['query']['connection_id']==cid) for cid in (1890,1888,726)};assert p['target_connection_ids']==list(targets);assert all(sha(v['path'])==v['sha256'] for v in new['inputs'].values());g=Path(new['inputs']['graph']['path']);audit=ImmutableXMLAudit(g,r['graph_sha256']);ids,classes,switches,_=read(g);unions=defaultdict(set);parents=defaultdict(dict);records={};ledger=Counter();history={int(n):c for n,c in r['history'].items()}
def accept(q,answer,record,checkcost):
 node=q['source'];used={node};incoming={};res,cap=classes[ids[node]];delay=res*cap/2;cost=0;other={n:c-int(n in unions[q['net_id']]) for n,c in ledger.items()};assert other.get(node,0)<audit.caps[node]
 for eid in answer['physical_edge_ids']:
  e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);assert other.get(node,0)<audit.caps[node];inc=arc_delay(classes,switches,ids[node],e.switch_id);delay+=inc;cost+=inc*r['scale']*(1+history.get(node,0))*(1+other.get(node,0));incoming[node]=(e.source,eid)
 assert node==q['sink'] and delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9)
 if checkcost:assert cost==answer['cost']
 net=q['net_id'];assert all(n not in parents[net] or parents[net][n]==v for n,v in incoming.items());parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]=record
for rec in prior['records']:
 if rec['net_id'] not in affected:
  q=b[rec['connection_id']];assert all(rec[k]==v for k,v in q.items());accept(q,rec['answer'],rec,False)
allunions=defaultdict(set)
for rec in prior['records']:
 allunions[rec['net_id']].add(rec['source'])
 for eid in rec['answer']['physical_edge_ids']:allunions[rec['net_id']].add(audit.graph.edges[eid].sink)
expected_affected={x['query']['net_id'] for x in targets.values()}
for cid,x in targets.items():
 nodes={x['query']['source']}|{audit.graph.edges[eid].sink for eid in x['physical_edge_ids']};blocked={n:sorted(net for net,ns in allunions.items() if net!=x['query']['net_id'] and n in ns) for n in nodes};blocked={n:owners for n,owners in blocked.items() if len(owners)>=audit.caps[n]};assert blocked=={int(n):owners for n,owners in p['blocked_owners'][str(cid)].items()};expected_affected.update(net for owners in blocked.values() for net in owners)
assert expected_affected==affected
queue=[x['query'] for x in targets.values()]+sorted((q for q in new['connections'] if q['net_id'] in affected and q['connection_id'] not in targets),key=lambda q:(q['net_id'],q['connection_id']))
for i,event in enumerate(r['events']):
 q=queue[i];assert q==event['query']
 if q['connection_id'] in targets and event['committed']:
  target=targets[q['connection_id']];assert event['answer']['physical_edge_ids']==target['physical_edge_ids'] and event['answer']['delay']==target['delay_integer']
 if event['committed']:accept(q,event['answer'],{**q,'mode':'INCREMENTAL_HISTORY_DELAY','answer':event['answer']},True)
 else:assert i==len(r['events'])-1 and r['failure']['query']==q
assert [records[c] for c in sorted(records)]==r['records'] and dict(ledger)=={int(n):c for n,c in r['ledger'].items()};assert all(c<=audit.caps[n] for n,c in ledger.items());(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'changed_connections':len(changed),'affected_nets':len(affected),'affected_connections':len(queue),'accepted_paths_checked':len(records),'events_checked':len(r['events']),'overflow_units':0,'multi_parent_nodes':0,'scope':'Independent originalXML path/endpoints/1ns/historycost/perNETunion event replay. Single criticalcoupled NET cohort audit; nativeFULL/STA and final timing remain unproven.'},indent=2)+'\n');print('verified',len(records),'paths;',len(changed),'changed endpoints;',len(queue),'affected cohort')
