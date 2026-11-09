"""All-RR-resource target-free root/blocking-owner pairs, no search or labels."""
import json,sys,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from zero_rc_budget_certificate_graph_v1 import load_graph
E=R/'experiments';I=E/'prospective_external_family_rejected_candidate_groups_v1_2026-10-20';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';D=E/'prospective_external_family_blocker_root_pair_schedule_v2_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 proof=read(I/'research_decision_v1.json');assert all(sha(p)==h for p,h in proof['bindings'].items());cases=read(A/'protocol.json')['cases'];graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);g=load_graph(graph);D.mkdir(exist_ok=False);bindings={str(I/'research_decision_v1.json'):sha(I/'research_decision_v1.json'),str(graph):sha(graph),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 def support(recs):
  ns=set()
  for q in recs:
   u=q['source'];ns.add(u);seen={u};delay=0
   for eid in q['answer']['physical_edge_ids']:assert g['us'][eid]==u;u=g['vs'][eid];assert u not in seen and g['caps'][u]>0;ns.add(u);seen.add(u);delay+=g['weights'][g['switches'][eid]]
   assert u==q['sink'] and delay==q['answer']['delay']<=q['budget_integer']
  return ns
 for c in cases:
  case=c['case'];depfile=I/case/'dependencies.json';dep=read(depfile);pool=set(dep['pool_NETs']);out=A/case/'native_retained/warm_timing_round_updated';statefile=out/'round1.json';receiptfile=out/'receipt.json';state=read(statefile);ledger={int(n):v for n,v in state['ledger'].items()};old=defaultdict(list)
  for q in state['records']:old[q['net_id']].append(q)
  oldsets={n:support(recs) for n,recs in old.items()};owners=defaultdict(set)
  for n,ns in oldsets.items():
   for u in ns:owners[u].add(n)
  assert {u:len(ns) for u,ns in owners.items()}==ledger;candidate={x['net_id']:x['rejected_records'] for x in read(receiptfile)['rounds'][1]['events'] if x['net_id'] in pool};assert set(candidate)==pool;pairs=defaultdict(set);reasons=defaultdict(lambda:defaultdict(set));rootkinds={};allkinds=Counter()
  for root in sorted(pool):
   new=support(candidate[root]);added=new-oldsets[root];removed=oldsets[root]-new;delta=sum(max(0,ledger.get(u,0)+1-g['caps'][u])-max(0,ledger.get(u,0)-g['caps'][u]) for u in added)+sum(max(0,ledger[u]-1-g['caps'][u])-max(0,ledger[u]-g['caps'][u]) for u in removed);assert delta>0;pressure_nodes={u for u in added if ledger.get(u,0)>=g['caps'][u]};assert pressure_nodes;rootkinds[root]=sorted({g['types'][u] for u in pressure_nodes})
   for u in sorted(pressure_nodes):
    assert owners[u];allkinds[g['types'][u]]+=1
    for owner in sorted(owners[u]):
     assert owner!=root;key=tuple(sorted((root,owner)));pairs[key].add(root);reasons[key][root].add(u)
  fanout={n:len(qs) for n,qs in old.items()};schedule=[dict(members=list(members),trigger_roots=sorted(roots),connections=sum(fanout[n] for n in members),maximum_member_fanout=max(fanout[n] for n in members),pressure_reasons=[dict(root=root,blocked_nodes=sorted(reasons[members][root])) for root in sorted(roots)]) for members,roots in sorted(pairs.items())];assert (3279,3280) in pairs;rootcoverage=set().union(*pairs.values());assert rootcoverage==pool;payload=D/case/'schedule.json';payload.parent.mkdir(parents=True);payload.write_text(json.dumps(schedule)+'\n');sizes=sorted(q['connections'] for q in schedule);row=dict(case=case,pressure_rejection_roots=len(pool),distinct_unordered_pairs=len(schedule),all_roots_covered=True,known_exchange_generated_without_special_case=True,pairs_with_owner_outside_candidate_pool=sum(any(n not in pool for n in q['members']) for q in schedule),total_scheduled_CID_visits=sum(sizes),pair_connections_median=sizes[len(sizes)//2],pair_connections_p95=sizes[(len(sizes)-1)*95//100],pair_connections_max=max(sizes),pairs_with_member_fanout_ge16=sum(q['maximum_member_fanout']>=16 for q in schedule),roots_without_CHANNEL_pressure=sum(not {'CHANX','CHANY'}.intersection(kinds) for kinds in rootkinds.values()),pressure_node_types=dict(allkinds));rows.append(row);print(json.dumps(row),flush=True)
  for p in [depfile,statefile,receiptfile,payload]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_ALL_RR_TARGET_FREE_ROOT_BLOCKER_PAIR_SCHEDULES_COMPLETE',rows=rows,bindings=bindings,policy='Every positive-pressure rebased root paired with every old owner of each added capacity-full RR node, all RR types. Deduplicate unordered pairs, stable numeric ordering. No label/search-result/quality filtering. Preparation only; execution/resource protocol pending.'),indent=2)+'\n')
if __name__=='__main__':main()
