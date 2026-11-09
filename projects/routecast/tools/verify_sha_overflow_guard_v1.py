"""Full current query and rejected path certificates, exact unchanged initial baseline and pressure gate replay."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_overflow_guard_v1_2026-10-10';bindings={str(Path(__file__)):sha(Path(__file__))}
def auth(v):
 for section in ['bindings','files']:assert all(sha(p)==h for p,h in v.get(section,{}).items())
for filename in ['receipt.json','protocol.json']:
 p=D/filename;v=json.loads(p.read_text());auth(v);bindings[str(p)]=sha(p)
protocol=json.loads((D/'protocol.json').read_text());rows=[]
for case,epfile in protocol['cases']:
 ep=json.loads(Path(epfile).read_text());queries={q['connection_id']:q for q in ep['connections']};assert len(queries)==6273;W=D/case/'model'
 for filename in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json','shared_audit_receipt.json','receipt.json','protocol.json']:
  p=W/filename;v=json.loads(p.read_text());auth(v);bindings[str(p)]=sha(p)
  if filename=='verification.json':assert v['complete_prospective_overflow_guard_rejected_candidate_and_unchanged_epoch_pass'] and v['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass'] and v['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
  if filename=='shared_audit_receipt.json':assert v['all_three_complete_audits_pass'] and v['fresh_independent_graph_context']
 initial=json.loads((W/'initial.json').read_text());base=R/'experiments/sha_price_factorial_ablation_v2_2026-10-10'/case/'both/model';assert initial==json.loads((base/'initial.json').read_text()) and json.loads((W/'floors.json').read_text())==json.loads((base/'floors.json').read_text());receipt=json.loads((W/'receipt.json').read_text());graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);owned=defaultdict(set);members=defaultdict(set);epochs={}
 def own(recs):return {q['source'] for q in recs}|{xml.graph.edges[e].sink for q in recs for e in q['answer']['physical_edge_ids']}
 for rec in initial['records']:owned[rec['net_id']].update(own([rec]));epochs[rec['net_id']]=1
 for net,ns in owned.items():
  for node in ns:members[node].add(net)
 counts=Counter()
 for rr in receipt['rounds']:
  for event in rr['events']:
   net=event['net_id'];assert epochs[net]==event['old_epoch'];counts[event['status']]+=1
   if event['status']=='RETAIN_BUDGET_OR_UNREACHABLE':assert event['new_epoch']==epochs[net];continue
   rejected=event['status']=='RETAIN_OVERFLOW_INCREASE';recs=event['rejected_records'] if rejected else event['records'];assert {r['connection_id'] for r in recs}=={cid for cid,q in queries.items() if q['net_id']==net}
   for rec in recs:assert {k:rec[k] for k in queries[rec['connection_id']]}==queries[rec['connection_id']]
   new=own(recs);old=owned[net];delta=sum(max(0,len(members[n])+int(n in new)-int(n in old)-xml.graph.nodes[n].capacity)-max(0,len(members[n])-xml.graph.nodes[n].capacity) for n in old|new);assert delta==event['prospective_overflow_delta']
   if rejected:assert delta>0 and event['new_epoch']==epochs[net] and 'records' not in event
   else:
    assert delta<=0 and event['status']=='COMMITTED' and 'rejected_records' not in event
    for node in old:members[node].remove(net)
    for node in new:members[node].add(net)
    owned[net]=new;epochs[net]+=1;assert event['new_epoch']==epochs[net]
  state=json.loads(Path(rr['state_file']).read_text());assert {n:len(ns) for n,ns in members.items() if ns}=={int(n):c for n,c in state['ledger'].items()} and epochs=={int(n):c for n,c in state['epochs'].items()}
  assert rr['overflow_after']<=rr['overflow_before']
 for filename in ['initial.json','sketch.json','round0.json','round1.json']:
  p=W/filename;state=json.loads(p.read_text());recs={q['connection_id']:q for q in state['records']};assert len(state['records'])==len(recs)==6273
  for cid,q in queries.items():assert {k:recs[cid][k] for k in q}==q
  bindings[str(p)]=sha(p)
 rows.append(dict(case=case,event_counts=dict(counts)));print(case,dict(counts),flush=True)
assert len(rows)==2 and all(sha(p)==h for p,h in bindings.items());(D/'independent_verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all2_full_query_models_rejected_candidate_certificates_and_monotonic_guard_pass=True,scope='Full prospective overflow guard, independent nodeNET membership and complete XML/Fraction path/event audits, unchanged initial floors. Not native or prediction gain proof.'),indent=2)+'\n')
