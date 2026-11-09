"""Independent node-to-NET membership replay of every transaction pressure delta."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_transaction_overflow_v1_2026-10-10';p=D/'diagnosis.json';v=json.loads(p.read_text());assert v['all_events_full_round_ledger_rebuild_pass'] and all(sha(q)==h for q,h in v['bindings'].items());bindings={str(p):sha(p),str(Path(__file__)):sha(Path(__file__))};checked=0
for case,root in [('original','sha1_actual_old_linear_expat_workflow_v1_2026-10-10'),('second_swap','sha_second_swap_complete_workflow_v1_2026-10-10')]:
 W=R/'experiments'/root/'seed/model/sha1';epfile=R/'experiments'/root/'seed/demand/sha1/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);initial=json.loads((W/'initial.json').read_text());members=defaultdict(set);owned=defaultdict(set)
 def nodes(recs):return {x['source'] for x in recs}|{xml.graph.edges[e].sink for x in recs for e in x['answer']['physical_edge_ids']}
 for rec in initial['records']:owned[rec['net_id']].update(nodes([rec]))
 for net,ns in owned.items():
  for n in ns:members[n].add(net)
 def excess(n):return max(0,len(members[n])-xml.graph.nodes[n].capacity)
 total=sum(excess(n) for n in members);receipt=json.loads((W/'receipt.json').read_text());derived=[];counts=Counter();units=Counter()
 for rr in receipt['rounds']:
  assert total==rr['overflow_before']
  for index,event in enumerate(rr['events']):
   net=event['net_id'];before=total;origin='retained';delta=0
   if event['status']=='COMMITTED':
    new=nodes(event['records']);old=owned[net];touched=old|new;cost=sum(excess(n) for n in touched)
    for n in old:assert net in members[n];members[n].remove(net)
    for n in new:assert net not in members[n];members[n].add(net)
    delta=sum(excess(n) for n in touched)-cost;owned[net]=new;total+=delta;origin='fallback' if event.get('fallback',{}).get('status')=='ACCEPT_STRICT_IMPROVEMENT' else 'primary'
   derived.append(dict(round=rr['round_index'],index=index,net_id=net,origin=origin,overflow_before=before,overflow_delta=delta,overflow_after=total));effect='increase' if delta>0 else 'decrease' if delta<0 else 'equal';counts[origin+'/'+effect]+=1;units[origin+'/'+effect]+=abs(delta);checked+=1
  assert total==rr['overflow_after']==sum(excess(n) for n in members)
  state=json.loads(Path(rr['state_file']).read_text());assert {n:len(nets) for n,nets in members.items() if nets}=={int(n):c for n,c in state['ledger'].items()}
 row=next(r for r in v['rows'] if r['case']==case);assert derived==row['events'] and dict(counts)==row['counts'] and dict(units)==row['absolute_change_units']
 for q in [graph,epfile,W/'receipt.json',W/'initial.json']:bindings[str(q)]=sha(q)
assert checked==10094 and all(sha(q)==h for q,h in bindings.items());(D/'independent_verification.json').write_text(json.dumps(dict(bindings=bindings,all10094_events_independent_nodeNET_membership_overflow_replay_pass=True,scope='Exact pressure effects of existing commits; not new policy/label inference or causal prediction result.'),indent=2)+'\n');print('ALL10094 TRANSACTION PRESSURE DELTAS PASS')
