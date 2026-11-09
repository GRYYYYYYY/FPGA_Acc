"""Exact pre-transaction owner counts and frozen-price omissions, not a new router."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
from immutable_channel_span_prices_v1 import channel_span_prices

def main():
 out=R/'experiments/mmc_transaction_competition_v1_2026-10-10';out.mkdir(exist_ok=False)
 bindings=closure([Path(__file__)])
 cases=[('original',R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10/model'),('structural',R/'experiments/mmc_structural_guard_complete_v1_2026-10-10/model')]
 for _,model in cases:
  p=model/'shared_audit_receipt.json';v=json.loads(p.read_text());assert v['all_three_complete_audits_pass'] and all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
 ep=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';endpoint=json.loads(ep.read_text());graph=Path(endpoint['inputs']['graph']['path']);bindings[str(ep)]=sha(ep);bindings[str(graph)]=sha(graph)
 xml=ImmutableXMLAudit(graph,endpoint['graph_sha256']);span=channel_span_prices(xml)
 def own(recs):
  nodes=set()
  for rec in recs:
   u=rec['source'];nodes.add(u)
   for eid in rec['answer']['physical_edge_ids']:
    edge=xml.graph.edges[eid];assert edge.source==u;u=edge.sink;nodes.add(u)
   assert u==rec['sink']
  return nodes
 result=[]
 for name,model in cases:
  receipt=json.loads((model/'receipt.json').read_text());initial=json.loads((model/'initial.json').read_text());groups=defaultdict(list)
  for rec in initial['records']:groups[rec['net_id']].append(rec)
  owners={net:own(recs) for net,recs in groups.items()};ledger=Counter(n for nodes in owners.values() for n in nodes)
  assert dict(ledger)=={int(n):v for n,v in initial['ledger'].items()}
  totals=defaultdict(Counter);rounds=[]
  for row in receipt['rounds']:
   statepath=Path(row['state_file']);state=json.loads(statepath.read_text());prices={int(n):v for n,v in state['prices'].items()};rt=defaultdict(Counter)
   for event in row['events']:
    status=event['status'];bucket=rt[status];bucket['events']+=1
    if status=='RETAIN_BUDGET_OR_UNREACHABLE':bucket['no_complete_budget_candidate']+=1;continue
    net=event['net_id'];records=event['records'] if status=='COMMITTED' else event['rejected_records'];new=own(records);old=owners[net];added=new-old;removed=old-new
    blocked={n for n in added if ledger[n]>=xml.caps[n]};relief={n for n in removed if ledger[n]>xml.caps[n]}
    delta=len(blocked)-len(relief);assert delta==event['prospective_overflow_delta']
    gap={n for n in blocked if prices.get(n,0)==span.get(n,0)}
    bucket['added_resource_visits']+=len(added);bucket['added_full_resource_visits']+=len(blocked);bucket['removed_overused_resource_visits']+=len(relief)
    bucket['added_full_without_any_history_overuse_price']+=len(gap);bucket['events_with_added_full_without_history_price']+=bool(gap)
    bucket['events_with_added_full']+=bool(blocked);bucket['prospective_overflow_delta_sum']+=delta
    if status=='COMMITTED':
     assert delta<=0
     for n in removed:
      ledger[n]-=1
      if not ledger[n]:del ledger[n]
     for n in added:ledger[n]+=1
     owners[net]=new
    else:assert status=='RETAIN_OVERFLOW_INCREASE' and delta>0
   assert dict(ledger)=={int(n):v for n,v in state['ledger'].items()} and ledger==Counter(n for nodes in owners.values() for n in nodes)
   for status,c in rt.items():totals[status].update(c)
   rounds.append(dict(round_index=row['round_index'],statuses={k:dict(v) for k,v in rt.items()}))
  for p in [model/'receipt.json',model/'initial.json',model/'round0.json',model/'round1.json']:bindings[str(p)]=sha(p)
  item=dict(case=name,totals={k:dict(v) for k,v in totals.items()},rounds=rounds);result.append(item);print(json.dumps(item),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (out/'verification.json').write_text(json.dumps(dict(bindings=bindings,cases=result,all_event_added_blocked_minus_removed_relief_matches_audited_guard=True,all_round_ledgers_rebuilt=True,scope='Recorded complete budget-safe candidates only; budget/unreachable retained events reported separately. Counts are node-per-event visits, not unique nodes. Whole-NET old ownership excluded on new resources; frozen history-price gap does not mean total cost zero or prove adding present penalties improves routing. No new search, labels, causal ablation or performance proof.'),indent=2)+'\n')
if __name__=='__main__':main()
