"""Independent inverse-owner selection, round recomputation and reversible fork."""
import collections,copy,json,random,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from overuse_owner_schedule_v1 import select
from pre_route_endpoints import sha

def main():
 out=R/'experiments/overuse_owner_schedule_core_v1_2026-10-18';out.mkdir(exist_ok=False);rng=random.Random(20261018);checks=0
 for trial in range(100):
  owned={n:set(rng.sample(range(12),rng.randrange(1,8))) for n in range(8)};inverse=collections.defaultdict(set)
  for net,ns in owned.items():
   for n in ns:inverse[n].add(net)
  ledger={n:len(nets) for n,nets in inverse.items()};caps=[rng.randrange(1,5) for _ in range(12)];saved=copy.deepcopy((owned,ledger,caps))
  for mask in range(256):
   dirty={n for n in range(8) if mask>>n&1};expected=set(dirty)
   for n,nets in inverse.items():
    if len(nets)>caps[n]:expected.update(nets)
   assert select(dirty,owned,ledger,caps)==sorted(expected) and (owned,ledger,caps)==saved;checks+=1
 owned={10:{0,1},20:{0,2},30:{1,3},40:{4}};caps=[1,2,1,1,1,1];ledger=collections.Counter(n for ns in owned.values() for n in ns);assert select({40},owned,ledger,caps)==[10,20,40];owned[10]={1,5};ledger=collections.Counter(n for ns in owned.values() for n in ns);assert select({40},owned,ledger,caps)==[40]
 try:select({99},owned,ledger,caps)
 except ValueError:pass
 else:raise AssertionError('unknown dirty NET')
 p=R/'tools/run_native_endpoint_owner_feedback_v1_2026_10_18.py';s=p.read_text();s=s.replace('from pre_route_endpoints import sha\nfrom overuse_owner_schedule_v1 import select as select_overuse_owners','from pre_route_endpoints import sha').replace("assert scheduling in ['all','local','overuse_owners']","assert scheduling in ['all','local']").replace("scheduling_policy='all_NETs_each_round' if scheduling=='all' else ('endpoint_dirty_plus_current_overuse_owners_each_round' if scheduling=='overuse_owners' else 'endpoint_closure_NETs_each_round')","scheduling_policy='all_NETs_each_round' if scheduling=='all' else 'endpoint_closure_NETs_each_round'").replace('affected=(select_overuse_owners(dirty,owned,ledger,f[\'capacities\']) if scheduling=="overuse_owners" else sorted(groups if scheduling=="all" else dirty))','affected=sorted(groups if scheduling=="all" else dirty)');assert s==(R/'tools/run_native_endpoint_v2_feedback_v1_2026_10_18.py').read_text();spec=R/'experiments/mmc_owner_expansion_candidate_protocol_v1_2026-10-18/protocol.json';bindings={str(q):sha(q) for q in [Path(__file__),p,R/'tools/overuse_owner_schedule_v1.py',R/'tools/run_native_endpoint_v2_feedback_v1_2026_10_18.py',spec]}
 with (out/'verification.json').open('x') as f:json.dump(dict(status='overuse_owner_inverse_selection_round_recompute_and_reversible_feedback_fork_pass',bindings=bindings,selection_checks=checks,nontransitive_and_nonsticky_scope_verified=True,original_feedback_source_exactly_recovered=True,scope='Scheduling only. Real all-event/model/quality checks remain required; no native policy or performance result.'),f,indent=2)
 print('OWNER SCHEDULE CORE PASS',checks,flush=True)
if __name__=='__main__':main()
