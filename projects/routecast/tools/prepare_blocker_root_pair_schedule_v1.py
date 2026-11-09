"""All target-free root/blocking-owner pairs, no candidate search or label reads."""
import json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_rejected_candidate_groups_v1_2026-10-20';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';D=E/'prospective_external_family_blocker_root_pair_schedule_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 proof=read(I/'research_decision_v1.json');assert all(sha(p)==h for p,h in proof['bindings'].items());D.mkdir(exist_ok=False);bindings={str(I/'research_decision_v1.json'):sha(I/'research_decision_v1.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for c in read(A/'protocol.json')['cases']:
  case=c['case'];depfile=I/case/'dependencies.json';dep=read(depfile);adj={int(n):set(v) for n,v in dep['adjacency'].items()};blocked={int(n):set(v) for n,v in dep['external_blockers'].items()};statefile=A/case/'native_retained/warm_timing_round_updated/round1.json';state=read(statefile);fanout=Counter(q['net_id'] for q in state['records']);pairs=defaultdict(set)
  for root in sorted(adj):
   for owner in sorted(adj[root]|blocked.get(root,set())):
    assert owner!=root and owner in fanout;pairs[tuple(sorted((root,owner)))].add(root)
  schedule=[dict(members=list(members),trigger_roots=sorted(roots),connections=sum(fanout[n] for n in members),maximum_member_fanout=max(fanout[n] for n in members)) for members,roots in sorted(pairs.items())];assert (3279,3280) in pairs;rootcoverage=set().union(*pairs.values());assert rootcoverage==set(adj);payload=D/case/'schedule.json';payload.parent.mkdir(parents=True);payload.write_text(json.dumps(schedule)+'\n');sizes=sorted(q['connections'] for q in schedule);row=dict(case=case,pressure_rejection_roots=len(adj),distinct_unordered_pairs=len(schedule),all_roots_covered=True,known_exchange_generated_without_special_case=True,pairs_with_owner_outside_candidate_pool=sum(any(n not in adj for n in q['members']) for q in schedule),total_scheduled_CID_visits=sum(sizes),pair_connections_median=sizes[len(sizes)//2],pair_connections_p95=sizes[(len(sizes)-1)*95//100],pair_connections_max=max(sizes),pairs_with_member_fanout_ge16=sum(q['maximum_member_fanout']>=16 for q in schedule));rows.append(row);print(json.dumps(row),flush=True)
  for p in [depfile,statefile,payload]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_TARGET_FREE_ROOT_BLOCKER_PAIR_SCHEDULES_COMPLETE',rows=rows,bindings=bindings,policy='Every baseline final positive-pressure root paired with every channel blocking owner; releaser and unresolved-retaining/outside owners included. Deduplicate unordered pairs, sort NET IDs and pair list. No target labels, search results or quality-based filtering. Preparation only; execution/resource protocol pending.'),indent=2)+'\n')
if __name__=='__main__':main()
