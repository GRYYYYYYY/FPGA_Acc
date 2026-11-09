"""Independent per-event replay, exact query/tree/RC and full demand rebuild verification."""
import sys,json
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
name=sys.argv[1];out=R/f'experiments/aes_frozen_estimates_v1_2026-10-08/{name}/resident';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());assert p['bindings']==r['bindings'];bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());seedfile=out/'initial.json';seed=json.loads(seedfile.read_text());records=defaultdict(list)
for x in seed['records']:records[x['net_id']].append(x)
endpoint=next(Path(k) for k in r['bindings'] if k.endswith('/endpoints.json'));ep=json.loads(endpoint.read_text());queries={q['connection_id']:q for q in ep['connections']};graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,digest=read(graph);assert digest==ep['graph_sha256'];from math import lcm
scale=1
for node in ids:
 a,b=classes[node];scale=lcm(scale,(a*b/2).denominator)
for eid in range(len(xml.graph.edges)):
 edge=xml.graph.edges[eid];scale=lcm(scale,arc_delay(classes,switches,ids[edge.sink],edge.switch_id).denominator)
assert p['price_unit_integer']==scale//(20*10**9);epochs={n:1 for n in records};prices=Counter();import xml.etree.ElementTree as ET
span_prices={}
for event,node in ET.iterparse(graph,events=('end',)):
 if node.tag=='node':
  if node.get('type') in {'CHANX','CHANY'}:
   loc=node.find('loc');span_prices[int(node.get('id'))]=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1
  node.clear()
prices.update(span_prices);checked=committed=retained=changed_trees=0

def ownership(recs):
 owned=set()
 for x in recs:owned.add(x['source']);owned.update(xml.graph.edges[eid].sink for eid in x['answer']['physical_edge_ids'])
 return owned

def rebuild():return Counter(node for recs in records.values() for node in ownership(recs))
ledger=rebuild();assert dict(ledger)=={int(n):v for n,v in seed['ledger'].items()}
owner_sets=defaultdict(set)
for net,recs in records.items():
 for node in ownership(recs):owner_sets[node].add(net)
for index,roundrow in enumerate(r['rounds']):
 assert index==roundrow['round_index'];changed={n:c-xml.graph.nodes[n].capacity for n,c in ledger.items() if c>xml.graph.nodes[n].capacity};assert changed=={int(n):c for n,c in roundrow['changed_nodes'].items()};assert sum(changed.values())==roundrow['overflow_before'];prices.update(changed);affected=sorted(n for n,recs in records.items() if ownership(recs).intersection(set(changed)|set(span_prices) if index==0 else changed));assert affected==roundrow['affected_nets']==[x['net_id'] for x in roundrow['events']]
 for event in roundrow['events']:
  net=event['net_id'];old=records[net];assert epochs[net]==event['old_epoch']
  if event['status']=='RETAIN_BUDGET_OR_UNREACHABLE':
   assert event['new_epoch']==epochs[net] and event['failed_connection_ids'] and set(event['failed_connection_ids'])<={x['connection_id'] for x in old};assert 'records' not in event;retained+=1
  else:
   assert event['status']=='COMMITTED' and not event['failed_connection_ids'];new=event['records'];changed_trees+=int(new!=old);assert len(new)==len(old) and {x['connection_id'] for x in new}=={x['connection_id'] for x in old};oldbyid={x['connection_id']:x for x in old};parents={}
   for rec in new:
    q=queries[rec['connection_id']];assert all(rec[k]==q[k] for k in q);assert rec['floor_integer']==oldbyid[rec['connection_id']]['floor_integer'] and rec['budget_integer']==oldbyid[rec['connection_id']]['budget_integer'];u=q['source'];used={u};a,b=classes[ids[u]];delay=a*b/2
    for eid in rec['answer']['physical_edge_ids']:
     edge=xml.graph.edges[eid];assert edge.source==u and edge.sink not in used and xml.graph.nodes[edge.sink].capacity>0;v=edge.sink;incoming=(u,eid);assert v not in parents or parents[v]==incoming;parents[v]=incoming;delay+=arc_delay(classes,switches,ids[v],edge.switch_id);used.add(v);u=v
    assert u==q['sink'];integer=delay*scale;assert integer.denominator==1 and integer.numerator==rec['answer']['delay']<=rec['budget_integer']
   delta=Counter(ledger);oldowned=ownership(old);newowned=ownership(new)
   for node in oldowned-newowned:
    delta[node]-=1;assert delta[node]>=0
    if delta[node]==0:del delta[node]
   for node in newowned-oldowned:delta[node]+=1
   records[net]=new;epochs[net]+=1;assert epochs[net]==event['new_epoch'];ledger=delta;committed+=1
   for node in oldowned:owner_sets[node].remove(net)
   for node in newowned:owner_sets[node].add(net)
   assert all(ledger.get(node,0)==len(owner_sets[node]) for node in oldowned|newowned)
  assert sum(map(len,records.values()))==len(queries);checked+=1
 assert ledger==rebuild() and ledger==Counter({node:len(nets) for node,nets in owner_sets.items() if nets})
 state=json.loads(Path(roundrow['state_file']).read_text());assert state['records']==sorted([x for recs in records.values() for x in recs],key=lambda x:x['connection_id']);assert {int(n):c for n,c in state['ledger'].items()}==dict(ledger);assert {int(n):c for n,c in state['prices'].items()}==dict(prices);assert {int(n):c for n,c in state['epochs'].items()}==epochs;assert roundrow['overflow_after']==sum(max(0,c-xml.graph.nodes[n].capacity) for n,c in ledger.items());print('PASS feedback replay',name,index,roundrow['overflow_after'],flush=True)
assert len(r['rounds'])==p['rounds']==2;c=json.loads((out/'sketch.json').read_text());assert c['records']==state['records'] and c['ledger']==state['ledger'] and not c['eligible_for_legal_route_commit'];assert c['completed_connections']==c['required_connections']==len(queries);assert c['overflow_units']==r['rounds'][-1]['overflow_after'];independent=Counter(node for recs in records.values() for x in recs for node in ownership([x]));assert dict(independent)=={int(n):v for n,v in c['independent_connection_ledger'].items()};assert c['overflow_nodes']==sum(cn>xml.graph.nodes[n].capacity for n,cn in ledger.items());assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass=True,complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass=True,events=checked,committed=committed,retained=retained,changed_trees=changed_trees,completed=len(queries),overflow_units=c['overflow_units'],scope='Physical complete demand state/replacement audit; each event compared against independent explicit node-to-NET owner sets, full original-path ledger rebuild at each actual runtime round frame. No per-event runtime ledger snapshot exists; no actual memory intermediate-state claim. Retained attempts carry no independent shortest/unreachable certificate; no failure infeasibility/weighted optimality/full reoptimization/heldout/native or netgain claim.'),indent=2)+'\n');print('PASS incremental feedback',checked,committed,retained,flush=True)
