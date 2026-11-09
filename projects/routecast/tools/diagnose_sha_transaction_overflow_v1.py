"""Every actual committed transaction overflow delta, exact touched-node update plus full round rebuild."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_transaction_overflow_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={str(Path(__file__)):sha(Path(__file__)),str(R/'tools/immutable_xml_prediction_audit.py'):sha(R/'tools/immutable_xml_prediction_audit.py')};rows=[]
for case,root in [('original','sha1_actual_old_linear_expat_workflow_v1_2026-10-10'),('second_swap','sha_second_swap_complete_workflow_v1_2026-10-10')]:
 B=R/'experiments'/root;proofpath=B/'verification.json';v=json.loads(proofpath.read_text());assert v['all_cases_both_complete_arms_authenticated'] and all(sha(q)==h for q,h in v['bindings'].items());W=B/'seed/model/sha1';epfile=B/'seed/demand/sha1/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);caps=xml.graph.nodes
 for q in [proofpath,epfile,graph,W/'initial.json',W/'receipt.json']:bindings[str(q)]=sha(q)
 def own(records):return {x['source'] for x in records}|{xml.graph.edges[e].sink for x in records for e in x['answer']['physical_edge_ids']}
 initial=json.loads((W/'initial.json').read_text());records=defaultdict(list)
 for rec in initial['records']:records[rec['net_id']].append(rec)
 owners={n:own(recs) for n,recs in records.items()};ledger=Counter(node for nodes in owners.values() for node in nodes);assert dict(ledger)=={int(n):c for n,c in initial['ledger'].items()}
 overflow=sum(max(0,c-caps[n].capacity) for n,c in ledger.items());events=[];counts=Counter();units=Counter();receipt=json.loads((W/'receipt.json').read_text())
 for rr in receipt['rounds']:
  assert overflow==rr['overflow_before']
  for index,e in enumerate(rr['events']):
   net=e['net_id'];before=overflow;delta=0;origin='retained'
   if e['status']=='COMMITTED':
    newown=own(e['records']);oldown=owners[net];updates={n:ledger[n]-1 for n in oldown-newown};updates.update({n:ledger[n]+1 for n in newown-oldown});assert all(c>=0 for c in updates.values())
    for n,c in updates.items():delta+=max(0,c-caps[n].capacity)-max(0,ledger[n]-caps[n].capacity)
    for n,c in updates.items():
     if c:ledger[n]=c
     else:ledger.pop(n)
    owners[net]=newown;records[net]=e['records'];overflow+=delta;origin='fallback' if e.get('fallback',{}).get('status')=='ACCEPT_STRICT_IMPROVEMENT' else 'primary'
   else:assert e['status']=='RETAIN_BUDGET_OR_UNREACHABLE'
   effect='increase' if delta>0 else 'decrease' if delta<0 else 'equal';counts[origin+'/'+effect]+=1;units[origin+'/'+effect]+=abs(delta);events.append(dict(round=rr['round_index'],index=index,net_id=net,origin=origin,overflow_before=before,overflow_delta=delta,overflow_after=overflow))
  rebuild=Counter(node for recs in records.values() for node in own(recs));assert ledger==rebuild and overflow==sum(max(0,c-caps[n].capacity) for n,c in rebuild.items())==rr['overflow_after'];statepath=Path(rr['state_file']);state=json.loads(statepath.read_text());assert dict(ledger)=={int(n):c for n,c in state['ledger'].items()} and sorted([x for recs in records.values() for x in recs],key=lambda x:x['connection_id'])==state['records'];bindings[str(statepath)]=sha(statepath)
 assert len(events)==sum(len(rr['events']) for rr in receipt['rounds']);rows.append(dict(case=case,counts=dict(counts),absolute_change_units=dict(units),events=events));print(case,dict(counts),dict(units),flush=True)
assert all(sha(q)==h for q,h in bindings.items());(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_events_full_round_ledger_rebuild_pass=True,scope='All actual transactions original+secondswap exposedSHA; fullgraph overflow, no native-label use for delta. Weighted fallback objective differs from overflow. Not causal prediction or new acceptance policy proof.'),indent=2)+'\n')
