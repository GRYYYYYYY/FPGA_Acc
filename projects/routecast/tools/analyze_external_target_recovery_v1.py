"""All42 observed target post-iteration recovery/stability, no selection policy."""
import json,csv,hashlib
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/prospective_external_family_native_growth_owner_observer_v1_2026-10-19';D=R/'experiments/prospective_external_family_target_recovery_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 v=json.loads((P/'trace_verification_v1.json').read_text());assert all(sha(p)==h for p,h in v['bindings'].items());D.mkdir(exist_ok=False);bindings={str(P/'trace_verification_v1.json'):sha(P/'trace_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 def path(q):return tuple(tuple(x.split(':')[:2]) for x in q['path_sink_to_source_node_switch_occ_hist_pres'].strip(',').split(',') if x)
 for i in (1,2,3):
  for arm in ('cold','seed'):
   case=f'w160/episode_{i:02d}/{arm}';p=P/case/'native/target_iterations.tsv';bindings[str(p)]=sha(p);targets=defaultdict(list)
   for r in csv.DictReader(p.open(),delimiter='\t'):
    if r['phase']=='AFTER':targets[(int(r['net']),int(r['pin']))].append(r)
   assert len(targets)==42
   for (net,pin),rs in targets.items():
    last=rs[-1];delay_start=path_start=len(rs)-1
    while delay_start>0 and rs[delay_start-1]['delay_s']==last['delay_s']:delay_start-=1
    while path_start>0 and path(rs[path_start-1])==path(last):path_start-=1
    changes=[dict(iteration=int(q['iteration']),delay_ns=float(q['delay_s'])*1e9,raw_criticality=float(q['criticality'])) for j,q in enumerate(rs) if j==0 or q['delay_s']!=rs[j-1]['delay_s']]
    rows.append(dict(case=case,net=net,pin=pin,name=last['name'],final_iteration=int(last['iteration']),final_delay_ns=float(last['delay_s'])*1e9,final_delay_stable_from=int(rs[delay_start]['iteration']),final_exact_path_stable_from=int(rs[path_start]['iteration']),delay_changes=changes))
 assert all(sha(p)==h for p,h in bindings.items());(D/'diagnosis.json').write_text(json.dumps(dict(status='ALL252_TARGET_RECOVERY_TRAJECTORIES_RECORDED',rows=rows,bindings=bindings,limitations='Stable path/delay does not establish skipped route calls or force-reroute status. Posthoc fixed target cohort; no fit or policy selection. Full native QoR remains failed.'),indent=2)+'\n');print('ALL252_TARGET_RECOVERY_TRAJECTORIES_RECORDED')
if __name__=='__main__':main()
