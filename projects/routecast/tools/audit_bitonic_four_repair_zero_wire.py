"""Independent XML sequential initial/repair query, release, history and ledger audit."""
import json
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_owned_four_repair_zero_wire_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items());rows=[]
for row in r['rows']:
 n=row['count'];file=out/f'n{n}.json';init=out/f'n{n}_initial.json';assert sha(file)==row['candidate_sha256'] and sha(init)==row['initial_sha256'];c=json.loads(file.read_text());initial=json.loads(init.read_text());epfile=next(Path(f) for f in p['inputs'] if Path(f).parent.name==f'n{n}');assert sha(epfile)==p['inputs'][str(epfile)];ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert all(sha(x['path'])==x['sha256'] for x in ep['inputs'].values());a=ImmutableXMLAudit(graph,c['graph_sha256']);ids,classes,switches,_=read(graph);queries={q['connection_id']:q for q in ep['connections']};unions=defaultdict(set);parents=defaultdict(dict);records={};history=Counter();count=0;releases=0
 def ledger():return Counter(node for used in unions.values() for node in used)
 def check(q,answer,commit,witness=False):
  nonlocal_placeholder=None
  assert q==queries[q['connection_id']];owner=unions[q['net_id']];demand=ledger();other={} if witness else {node:used-int(node in owner) for node,used in demand.items()}
  if answer['status']!='FOUND':assert not commit;return
  node=q['source'];used={node};incoming={};res,cap=classes[ids[node]];delay=res*cap/2;cost=F(0)
  if not witness:assert other.get(node,0)<a.caps[node]
  for eid in answer['physical_edge_ids']:
   e=a.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);inc=arc_delay(classes,switches,ids[node],e.switch_id);delay+=inc;penalty=F(p['weight_ns'])*a.spans[node]/10**9 if a.types[node] in (4,5) and node not in owner else F(0);cost+=(inc*(1+history[node])**2+penalty)*c['scale']*(1+other.get(node,0));incoming[node]=(e.source,eid)
   if not witness:assert other.get(node,0)<a.caps[node]
  assert node==q['sink'] and delay==F(answer['delay'],c['scale'])<=F(1,10**9) and cost==answer['cost']
  if commit:
   assert q['connection_id'] not in records and all(node not in parents[q['net_id']] or parents[q['net_id']][node]==x for node,x in incoming.items());parents[q['net_id']].update(incoming);owner.update(used);records[q['connection_id']]={**q,'answer':answer}
 for k,e in enumerate(initial['attempts']):
  assert e['query']==sorted(ep['connections'],key=lambda q:(q['net_id'],q['connection_id']))[k];assert e['wire_owner_union']==sorted(unions[e['query']['net_id']]);check(e['query'],e['native_answer'],k<len(initial['records']));count+=1
 assert dict(ledger())=={int(k):v for k,v in initial['ledger'].items()};assert set(records)=={x['connection_id'] for x in initial['records']}
 if c.get('events') is not None:
  for e in c['events']:
   if e['type'] in ('QUERY','BUDGET_WITNESS'):
    assert e['wire_owner_union']==sorted(unions[e['query']['net_id']]);check(e['query'],e['answer'],e.get('committed',False),e['type']=='BUDGET_WITNESS');count+=1
   elif e['type']=='RELEASE':
    net=e['failed_query']['net_id'];demand=ledger();assert all(demand[node]-int(node in unions[net])>=a.caps[node] for node in e['frontier']);owners={node:sorted(k for k,used in unions.items() if k!=net and node in used) for node in e['frontier']};assert owners=={int(k):v for k,v in e['owners'].items()};blockers=sorted({net for owned in owners.values() for net in owned});assert blockers==e['blocker_NETs'];removed=sorted(cid for cid,record in records.items() if record['net_id'] in blockers);assert removed==e['removed_connection_ids']
    for net in blockers:assert sorted(unions[net])==e['released_unions'][str(net)];del unions[net];del parents[net]
    for cid in removed:del records[cid]
    history.update(e['frontier']);assert dict(history)=={int(k):v for k,v in e['history_after'].items()};assert {node:h*(h+2) for node,h in history.items()}=={int(k):v for k,v in e['effective_history_after'].items()};releases+=1
   else:raise AssertionError('unknown event')
 assert releases==c.get('repairs',0)<=4;assert dict(history)=={int(k):v for k,v in c['history'].items()};assert dict(ledger())=={int(k):v for k,v in c['ledger'].items()};assert len(records)==c['completed_connections'];assert set(records)=={x['connection_id'] for x in c['records']}
 for x in c['records']:assert all(x[k]==v for k,v in records[x['connection_id']].items())
 assert (c['failure'] is None)==(len(records)==len(queries));rows.append(dict(count=n,query_events_checked=count,releases=releases,final_connections=len(records),required=len(queries),status=c['status'],prefix_overflow_units=0));print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),auditor_sha256=sha(Path(__file__)),rows=rows,scope='Allcase originalXML path/cost/owner/history/capacity/tree/ledger replay, release blockers and removedrecords exact. No global search completeness/failure minimality or nativecandidate QoR/gain.'),indent=2)+'\n')
